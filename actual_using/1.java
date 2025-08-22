package com.huawei.aiservice.impl.strategy;

import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.huawei.aiservice.constants.PromptConstant;
import com.huawei.aiservice.entity.pojo.Defect;
import com.huawei.aiservice.entity.pojo.FileEntity;
import com.huawei.aiservice.entity.pojo.FileRule;
import com.huawei.aiservice.entity.pojo.Rule;
import com.huawei.aiservice.enums.ReportStatus;
import com.huawei.aiservice.exception.BusinessException;
import com.huawei.aiservice.service.DefectService;
import com.huawei.aiservice.service.FileRuleService;
import com.huawei.aiservice.thread.FileRuleCallable;
import com.huawei.aiservice.utils.AIUtils;
import com.huawei.aiservice.utils.ConvertUtils;
import com.vladsch.flexmark.ast.FencedCodeBlock;
import com.vladsch.flexmark.parser.Parser;
import com.vladsch.flexmark.util.ast.Document;
import com.vladsch.flexmark.util.ast.Node;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

@Slf4j
public abstract class ParentCallable implements FileRuleCallable<List<Defect>> {
    public final String systemPrompt;

    public final FileRuleService fileRuleService;

    public final DefectService defectService;


    public final FileEntity fileEntity;

    public final Rule rule;

    public final String fragment;

    @Override
    public List<Defect> call() throws Exception {
        Parser parser = Parser.builder().build();
        File inputFile = new File(fileEntity.getFilePath());
        String inputString = new String(Files.readAllBytes(Paths.get(inputFile.getAbsolutePath())));
        Document document = parser.parse(inputString);

        LambdaUpdateWrapper<FileRule> selectWrapper = Wrappers.<FileRule>lambdaUpdate().eq(FileRule::getFileId,
                fileEntity.getFileId()).eq(FileRule::getRuleId, rule.getRuleId());
        FileRule fileRule = fileRuleService.getOne(selectWrapper);
        List<Defect> result = new ArrayList<>();

        try {
            if (StringUtils.isBlank(fragment)) {
                result = callFileCheck(document, fileRule);
            } else {
                result = callFragmentCheck(fragment, fileRule);
            }
        } catch (Exception e) {
            String ruleName = rule.getRuleName();
            log.error(ruleName + " error", e);
        }


        // 更新fileRule的状态
        LambdaUpdateWrapper<FileRule> wrapper = Wrappers.<FileRule>lambdaUpdate().eq(FileRule::getFileRuleId,
                        fileRule.getFileRuleId())
                .set(FileRule::getCheckStatus, ReportStatus.SUCCESS);
        fileRuleService.update(wrapper);

        return result;
    }

    /**
     * 不需要上下文
     *
     * @param fileString
     * @param fileRule
     * @return
     */
    @Override
    public List<Defect> callFragmentCheck(String fileString, FileRule fileRule) throws Exception {
        List<Defect> defectList;
        try {
            defectList = solve(systemPrompt, fileRule.getFileRuleId(), fragment);
        } catch (Exception e) {
            log.error("fragment check error", e);
            throw new BusinessException("fragment check error", e);
        }
        return defectList;
    }

    /**
     * 不需要上下文
     *
     * @param document
     * @param fileRule
     * @return
     */
    @Override
    public List<Defect> callFileCheck(Document document, FileRule fileRule) {
        List<Defect> result = new ArrayList<>();
        StringBuilder checkString = new StringBuilder();
        // 遍历AST节点
        for (Node node : document.getChildren()) {
            if (node instanceof FencedCodeBlock) continue;
            try {
                checkString.append(node.getChars().toString());
                if (checkString.length() < PromptConstant.fragmentSize) {
                    continue;
                }
                List<Defect> defectList = solve(systemPrompt, fileRule.getFileRuleId(), checkString.toString());
                result.addAll(defectList);
                // checkString清空
                checkString.delete(0, checkString.length());
            } catch (Exception e) {
                log.error("thread error", e);
            }
        }

        if (checkString.length() > 0) {
            try {
                List<Defect> defectList = solve(systemPrompt, fileRule.getFileRuleId(), checkString.toString());
                result.addAll(defectList);
            } catch (Exception e) {
                log.error("thread error", e);
            }
        }

        return result;
    }

    public ParentCallable(String systemPrompt, FileRuleService fileRuleService, DefectService defectService, FileEntity fileEntity, Rule rule, String fragment) {
        this.systemPrompt = systemPrompt;
        this.fileRuleService = fileRuleService;
        this.defectService = defectService;
        this.fileEntity = fileEntity;
        this.rule = rule;
        this.fragment = fragment;
    }

    public List<Defect> solve(String updateSystemPrompt, int fileRuleId, String nodeString) throws Exception {
        String responseJson = null;
        while (responseJson == null &&
                fileRuleService.getById(fileRuleId).getCheckStatus().equals(ReportStatus.PROCESSING)) {
            responseJson = AIUtils.getResponse(updateSystemPrompt, nodeString);
        }
        List<Defect> defectList = ConvertUtils.convert(responseJson);
        List<Defect> result = new ArrayList<>();
        for (Defect defect : defectList) {
            File file = new File(fileEntity.getFilePath());
            int lineNum = getLineNum(file, defect.getProblematicSentence());
            if (lineNum == -1) {
                continue;
            }
            boolean isValid = checkIsValid(defect, nodeString);
            if (!isValid) {
                continue;
            }
            defect.setProblematicLineNum(lineNum);
            defect.setFileRuleId(fileRuleId);
            result.add(defect);
        }

        // 保存
        defectService.saveBatch(result);
        return result;
    }

    public int getLineNum(File file, String target) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(Files.newInputStream(file.toPath())))) {
            String line;
            int lineNumber = 0;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                if (line.contains(target)) {
                    return lineNumber;
                }
            }
        } catch (IOException e) {
            log.error("Error reading file", e);
            return -1;
        }
        return -1; // 如果未找到目标字符串，返回 -1
    }

    public boolean checkIsValid(Defect defect, String nodeString) {
        boolean result = true;
        String problematicSentence = defect.getProblematicSentence();
        if (problematicSentence.equals(defect.getFixedSentence())) {
            result = false;
        }
        if (!nodeString.contains(problematicSentence)) {
            result = false;
        }

        return result;
    }

}
