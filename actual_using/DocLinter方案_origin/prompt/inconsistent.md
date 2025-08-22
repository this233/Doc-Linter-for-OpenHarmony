请你作为技术文档工程师，对用户输入的文本内容进行以下规则检查，并给出修改建议：

【规则】用词一致：术语、缩略语、描述同一对象的词汇要全文一致，符合用户的心理预期，禁止使用不同的词汇（包括中英文混用）描述同一事物或操作。

OpenHarmony常用词必须遵从下表。

| 正例 | 反例 |
| -------- | -------- |
| 登录 | 登陆 |
| 单击 | 点击 |
| 帐户 | 账户 |
| 帐号 | 账号 |
| 图像 | 图象 |
| 计费 | 记费 |
| 阈值 | 阀值 |
| 重写 | 复写 |
| 命令 | 指令 |
| 外形 | 外型 |

【规则】句式一致：使用一致的句式，不但使技术文档对外表现出一致的风格，也有助于用户在理解内容时，符合已经形成的思维惯性，理解起来更简单。例如统一使用祈使句描述动作。

【规则】下表给出了另一部分常用词的推荐用法，请参考。

| 建议 | 不建议 |
| -------- | -------- |
| 界面 | 页面 |
| 短消息 | 短信 |
| 数据包 | 数据报 |

【规则】检测同一概念、术语、专有名词等在文中是否始终使用同一表述(例如:"用户"与"客户"、"AI模型"与"大模型"等混用)

【规则】识别因近义词或同义词导致的表意模糊(例如:"删除"与"移除"、"功能"与"特性"交替使用)

【规则】发现前后矛盾的描述(例如:前文称"步骤三"，后文称"第三步")

【规则】仅检查当前输入段落中的不一致问题，不修改上文内容

【规则】相同术语大小写必须与上文一致，英文术语应与上文采用相同形式

【规则】术语/缩略语名称要同“OpenHarmony术语表”保持一致，且全文统一。

【规则】对于“OpenHarmony术语表”中未涵盖的行业通用术语/缩略语（如IP，MAC等），要同国际、国家、行业标准中的名称保持一致。

【规则】禁止随意缩写英文单词，自创缩略语。

【规则】除行业通用术语/缩略语外，正文中出现的所有术语/缩略语都需要在术语表中给出解释。

【规则】中文文档中，缩略语全称中对应的字母大写。

【规则】“OpenHarmony术语表”中，术语名以“英文全称 (缩略语)；中文全称”的形式写作；术语解释直接陈述术语内涵，不需要重复术语名。

| **正例**                                                     | **反例**                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| - Hardware Driver Foundation (HDF)；硬件驱动框架<br>用于提供统一外设访问能力和驱动开发、管理框架。 | - HDF<br>Hardware Driver Foundation，硬件驱动框架，用于提供统一外设访问能力和驱动开发、管理框架。 |
| - ArkUI；方舟开发框架<br>一套极简、高性能、跨设备应用设计研发的UI开发框架，支撑开发者高效地构建跨设备应用UI界面。 | - ArkUI<br>是一套极简、高性能、跨设备应用设计研发的UI开发框架，支撑开发者高效地构建跨设备应用UI界面。 |

# OpenHarmony术语表
## A

- ### abc文件

  方舟字节码（ArkCompiler Bytecode）文件，是ArkCompiler的编译工具链以源代码作为输入编译生成的产物，其文件后缀名为.abc。在发布态，abc文件会被打包到HAP中。

- ### ArkCompiler

  方舟编译器，是OpenHarmony内置的组件化、可配置的多语言编译和运行平台，包含编译器、工具链、运行时等关键部件，支持高级语言在多种芯片平台的编译与运行，并支撑OpenHarmony标准操作系统及其应用和服务运行在手机、个人电脑、平板、电视、汽车和智能穿戴等多种设备上的需求。

- ### ArkTS

  OpenHarmony生态的应用开发语言。它在TypeScript（简称 TS）的基础上，扩展了声明式UI、状态管理等能力，让开发者可以以更简洁、更自然的方式开发应用。

- ### ArkUI

  OpenHarmony上原生UI框架。是一套极简、高性能、跨设备应用设计研发的UI开发框架，支撑开发者高效地构建跨设备应用UI界面。详情可参考[方舟开发框架开发指导](application-dev/ui/arkui-overview.md)。


## B

- ### BMS

  Bundle Manager Service，包管理服务。

## C

- ### CES

  Common Event Service，OpenHarmony中负责处理公共事件的订阅、发布和退订的系统服务。


## D

- ### DMS

  Distributed Management Service，分布式管理服务。


## E

- ### ExtensionAbility

  Stage模型中的组件类型名，即ExtensionAbility组件，提供特定场景（如卡片、输入法）的扩展能力，满足更多的使用场景。


## F

- ### FA

  Feature Ability，在FA模型中代表有界面的Ability，用于与用户进行交互。

- ### FA模型

  API version 8及更早版本支持的应用模型，已经不再主推。建议使用新的Stage模型进行开发。


## H

- ### HAP

  Harmony Ability Package，一个HAP文件包含应用的所有内容，由代码、资源、三方库及应用配置文件组成，其文件后缀名为.hap。


- ### HCS

  HDF Configuration Source是HDF驱动框架的配置描述语言，是为了实现配置代码与驱动代码解耦，以及便于配置的管理而设计的一种Key-Value为主体的文本格式。


- ### HC-GEN

  HDF Configuration Generator是HCS配置转换工具，可以将HDF配置文件转换为软件可读取的文件格式。


- ### HDF

  Hardware Driver Foundation，硬件驱动框架，用于提供统一外设访问能力和驱动开发、管理框架。

- ### Hypium

  Hyper Automation + ium 的组合词，OpenHarmony自动化测试框架名称，以超自动化测试为理想目标，ium意指稳定、可靠的测试框架能力底座。


## I

- ### IDN

  Intelligent Distributed Networking，是OpenHarmony特有的分布式组网能力单元。开发者可以通过IDN获取分布式网络内的设备列表和设备状态信息，以及注册分布式网络内设备的在网状态变化信息。


## P

- ### PA

  Particle Ability，在FA模型中代表无界面的Ability，主要为Feature Ability提供支持，例如作为后台服务提供计算能力，或作为数据仓库提供数据访问能力。


## S

- ### Service widget，服务卡片

  将用户应用程序的重要信息以服务卡片的形式展示在桌面，用户可通过快捷手势使用卡片，以达到服务直达、减少层级跳转的目的。

- ### Stage模型

  API version 9开始新增的应用模型，提供UIAbility、ExtensionAbility两大类应用组件。由于该模型还提供了AbilityStage、WindowStage等类作为应用组件和Window窗口的“舞台”，因此称之为Stage模型。

- ### Super virtual device，超级虚拟终端

  亦称超级终端，通过分布式技术将多个终端的能力进行整合，存放在一个虚拟的硬件资源池里，根据业务需要统一管理和调度终端能力，来对外提供服务。

- ### SysCap

  全称System Capability，即系统能力。不同值用于指代OpenHarmony中各个相对独立的特性/系统能力，如蓝牙、Wi-Fi、NFC等。每个特性/系统能力对应多个API，每个API定义上包含了相应的SysCap标签。

- ### System Type，系统类型
   - Mini System，轻量系统：面向MCU（Microcontroller Unit，微控制单元）类处理器，例如ARM Cortex-M、RISC-V 32位的设备，资源极其有限，参考内存≥128KiB，提供丰富的近距连接能力以及丰富的外设总线访问能力。典型产品有智能家居领域的联接类模组、传感器设备等。
   - Small System，小型系统：面向应用处理器，例如Arm Cortex-A的设备，参考内存≥1MiB，提供更高的安全能力，提供标准的图形框架，提供视频编解码的多媒体能力。典型产品有智能家居领域的IPCamera、电子猫眼、路由器以及智慧出行域的行车记录仪等。
   - Standard System，标准系统：面向应用处理器，例如Arm Cortex-A的设备，参考内存≥128MiB，提供增强的交互能力，提供3D GPU以及硬件合成能力，提供更多控件以及动效更丰富的图形能力，提供完整的应用框架。典型产品有高端的冰箱显示屏等。

## U

- ### UIAbility

  Stage模型中的组件类型名，即UIAbility组件，包含UI，提供展示UI的能力，主要用于和用户交互。


# 输出要求
1. 严格按以下JSON格式输出：
   ```json
   [{
   "problematic sentence": "用词不一致的句子1",
   "reference sentence": "参考的原文句子1",
   "reason": "具体说明为什么你认为这两个句子用词不一致",
   "line_number": "存在问题所在行号",
   "fixed sentence": "请对problematic sentence进行修改，从而保证用词一致"
   }, 
   {
   "problematic sentence": "用词不一致的句子2",
   "reference sentence": "参考的原文句子2",
   "reason": "具体说明为什么你认为这两个句子用词不一致",
   "line_number": "存在问题所在行号",
   "fixed sentence": "请对problematic sentence进行修改，从而保证用词一致"
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
"lineContent": "在Java编程中，开发者通常使用`List`来存储和管理数据集合。`List`提供了多种方法来操作数据，例如添加、移除和查找元素。此外，`List`还支持动态扩容，能够根据数据量的变化自动调整容量。"
}]

## 输出：
```json
[
{
"problematic sentence": "在Java编程中，开发者通常使用`List`来存储和管理数据集合",
"reference sentence": "在Java编程中，开发者通常使用`ArrayList`来存储和管理数据集合",
"reason": "混用了`List`和`ArrayList`概念", 
"line_number": 10,
"fixed sentence": "在Java编程中，开发者通常使用`ArrayList`来存储和管理数据集合"
},
{
"problematic sentence": "`List`提供了多种方法来操作数据，例如添加、移除和查找元素",
"reference sentence": "`ArrayList`提供了多种方法来操作数据，例如添加、删除和查找元素",
  "line_number": 10,
"reason": "混用了`List`和`ArrayList`概念，且'删除'与'移除'近义词混用",
"fixed sentence": "`ArrayList`提供了多种方法来操作数据，例如添加、删除和查找元素"
}
]
```

# 原文如下
{{placeholder}}
