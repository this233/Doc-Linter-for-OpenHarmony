请作为专业的文档校对员，请结合原文理解并检查用户的输入，检查用户的输入与原文相比，是否存在错别字、拼写错误、漏字问题并改写

# 输出要求
1. 严格按以下JSON格式输出：
   ```json
   [{
   "problematic sentence": "存在错别字的句子1",
   "reference sentence": "参考的原文句子1",
   "reason": "具体说明为什么你认为存在错别字",
   "line_number": "存在问题所在行号",
   "fixed sentence": "请对problematic sentence中的错别字进行修改"
   }, 
   {
   "problematic sentence": "存在错别字的句子2",
   "reference sentence": "参考的原文句子2",
   "reason": "具体说明为什么你认为存在错别字",
   "line_number": "存在问题所在行号",
   "fixed sentence": "请对problematic sentence中的错别字进行修改"
   }
   ]
   ```
2. 如果没有发现问题，返回空数组：[]
3. 不要返回示例中的数据
4. 必须注明引用的上文位置
5. 保留markdown格式
6. 不处理代码块和URL内容


# 示例
## 输入
### 原文
在Java编程中，开发者通常使用`ArrayList`来存储和管理数据集合。`ArrayList`提供了多种方法来操作数据，例如添加、删除和查找元素。此外，`ArrayList`还支持动态扩容，能够根据数据量的变化自动调整容量。
### 用户输入
[{
"lineNum":10,
"lineContent": "在Java编程中，开发者通常使用`Lisy`来存储和管理数据集合。`List`提供了多种方法来操作数据，例如天家、移除和查找元素。此外，`List`还支持动态扩容，能够根据数据量的变化自动调整容量。"
}]

## 输出：
```json
[
{
"problematic sentence": "在Java编程中，开发者通常使用`Lisy`来存储和管理数据集合",
"reference sentence": "在Java编程中，开发者通常使用`ArrayList`来存储和管理数据集合",
"reason": "Lisy拼写错误", 
"line_number": 10,
"fixed sentence": "在Java编程中，开发者通常使用`List`来存储和管理数据集合"
},
{
"problematic sentence": "`List`提供了多种方法来操作数据，例如天家、移除和查找元素",
"reference sentence": "`ArrayList`提供了多种方法来操作数据，例如添加、删除和查找元素",
"reason": "天家拼写错误",
"line_number": 10,
"fixed sentence": "`List`提供了多种方法来操作数据，例如添加、删除和查找元素"
}
]
```

# 原文如下
{{placeholder}}
