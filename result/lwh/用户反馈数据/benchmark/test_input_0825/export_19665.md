# ArkTS1.2语法迁移规则

ArkTS1.2在引入了静态类型系统、增强的并发能力的同时，也引入了与ArkTS1.1在语法和语义上的一部分差异。本文罗列了所有在ArkTS1.2中被限制的ArkTS1.1特性，并提供了重构代码的建议。

## 限定关键字

**规则：** `arkts-invalid-identifier`

**规则解释：**

ArkTS1.2中不能使用关键字或保留字作为变量、函数或类型的名称。

**变更原因：**

ArkTS1.2严格定义了关键字和保留字，代码中不能将其用作变量、函数或类型的名称。

以下关键字不能用作变量或函数的名称：
```
abstract else internal static as enum launch switch async export let super await extends native this break false new throw case final null true class for override try const function package undefined constructor if private while continue implements protected default import public do interface return boolean double number Boolean Double Number byte float object Byte Float Object bigint int short Bigint Int Short char long string Char Long String void
```
以下关键字不能用作类型的名称：
```
Awaited NoInfer Pick ConstructorParameters NonNullable ReturnType Exclude Omit ThisParameterType Extract OmitThisParameter ThisType InstanceType Parameters Capitalize Uncapitalize Lowercase Uppercase ArrayBufferTypes Function Proxy AsyncGenerator Generator ProxyHandler AsyncGeneratorFunction GeneratorFunction Symbol AsyncIterable IArguments TemplateStringsArray AsyncIterableIterator IteratorYieldResult TypedPropertyDescriptor AsyncIterator NewableFunction CallableFunction PropertyDescriptor
```

**适配建议：**

请将用到关键字或保留字的变量、函数或类型重命名。

**示例：**

**ArkTS1.1**
```typescript
let as: number = 1;
const abstract: string = "abstract";
```

**ArkTS1.2**
```typescript
let a = 1;
const abstract1: string = "abstract";
```

## 数值类型语义变化

**规则：** `arkts-numeric-semantic`

**规则解释：**

ArkTS1.2中整型数字字面量默认是int类型。

**变更原因：**

在ArkTS1.1中只有一个数字基础类型number，不区分整型字面量或是浮点型字面量。

在ArkTS1.2中，整型数字字面量默认是int类型，以提高执行效率。

**适配建议：**

建议开发者为数值类型变量添加明确的类型标注。

**示例：**

**ArkTS1.1**
```typescript
let n = 1;
console.log(String(n / 2))  // 0.5

let arr = [1, 2, 3];

function multiply(x = 2, y = 3) { // 需要明确类型
  return x * y;
}

function divide(x: number, y: number) {
  return x / y;
} // 函数返回值

let num = Math.floor(4.8); // num 可能是 int
let value = parseInt("42"); // value 可能是 int

function identity<T>(value: T): T {
  return value;
}
identity(42); // 42 可能推导为 int
```

**ArkTS1.2**
```typescript
let n: number = 1;
console.log(n / 2)  // output: 0.5

let m = 1;
console.log(m / 2)  // output: 0

let arr: number[] = [1, 2, 3];

function multiply(x: number = 2, y: number = 3): number {
  return x * y;
}

function divide(x: number, y: number): number {
  return x / y;
}

let num: number = Math.floor(4.8);
let value: number = parseInt("42");

function identity<T>(value: T): T {
  return value;
}
identity(42 as number);
```

## void类型只能用在返回类型的场景

**规则：** `arkts-limited-void-type`

**规则解释：**

在ArkTS1.1中，`void`是一个类型。在ArkTS1.2中，`void`不再是类型，它没有实体，只能用作函数、方法和lambda表达式的返回类型，表示不返回任何值。

**变更原因：**

在ArkTS1.1中，void类型可以在多个场景中使用。

在ArkTS1.2中，void只能使用在返回类型的场景，且void类型没有实体。

**适配建议：**

不要在函数返回类型之外的场景下使用void。

**示例：**

**ArkTS1.1**
```typescript
// 示例1：void类型变量声明
let s: void = foo();

// 示例2：void联合类型
let t: void | number = foo();

// 示例3：泛型参数中使用void
function process<T>(input: T): T {
  return input;
}
let result = process<void>(foo());

// 示例4：类型别名
type VoidAlias = void;

// 示例5：对象属性
let { x }: { x: void } = { x: foo() };

// 示例6：void类型参数
function execute(callback: void) {
  callback();
}

// 示例7：类型断言
let x = fun() as void;

// 示例8：函数返回类型
function foo(): void{};
```

**ArkTS1.2**
```typescript
// 函数返回类型-普通函数
function foo(): void {}
foo();

// 函数返回类型-箭头函数
function execute(callback: () => void) {
  callback();
}
execute(foo);
```

## 不支持void操作符

**规则：** `arkts-no-void-operator`

**规则解释：**

ArkTS1.2不支持void操作符获取undefined。

**变更原因：**
 
在ArkTS1.2中，undefined是关键字，不能用作变量名称，因此无需使用void操作符获取undefined。

**适配建议：**

使用IIFE（立即执行函数表达式）来执行运算符的表达式，并返回undefined。

**示例：**

**ArkTS1.1**
```typescript
let s = void 'hello';
console.log(s);  // output: undefined

let a = 5;
let b = void (a + 1);

function logValue(value: any) {
    console.log(value);
}
logValue(void 'data');

let fn = () => void 0;
```

**ArkTS1.2**
```typescript
(() => {
    'hello'
    return undefined;
})()

let a = 5;
let b = (() => {
    a + 1;
    return undefined;
})();  // 替换为 IIFE

logValue((() => {
    'data';
    return undefined;
})());  // 替换为 IIFE

let fn = () => undefined;  // 直接返回 `undefined`
```

## 限定使用字面量类型

**规则：** `arkts-limited-literal-types`

**规则解释：**

ArkTS1.2不支持数字字面量类型和布尔字面量类型。

**变更原因：**

ArkTS1.2提供更细化的数值类型供开发者选择，关注数值范围而非特定数字值，同时简化代码，避免歧义，不引入复杂数值字面量类型语法。
 
**适配建议：**

请使用number和boolean类型替代字面量类型。

**示例：**

**ArkTS1.1**
```typescript
let n1: 1 = 1;
let n2: 0.1 = 0.1;
let f: true = true;

function getOne(): 1 {
  return 1; 
}
function isAvailable(): true {
  return true;
}

function setFlag(flag: true) {
  console.log(flag);
}
function setPrecision(precision: 0.1) {
  console.log(precision);
}

interface Config {
  readonly enable: true;
  readonly threshold: 100;
}
```

**ArkTS1.2**
```typescript
let n1: int = 1;
let n2: number = 0.1;
let f: boolean = true;

function getOne(): int {
  return 1;
}
function isAvailable(): boolean {
  return true;
}

function setFlag(flag: boolean) {
  console.log(flag);
}
function setPrecision(precision: number) {
  console.log(precision);
}

interface Config {
  readonly enable: boolean;
  readonly threshold: int;
}
```

## 不支持arguments对象

**规则：** `arkts-no-arguments-obj`

**规则解释：**

ArkTS1.2不支持通过arguments对象获取参数。

**变更原因：**

ArkTS1.2对函数调用进行严格参数检查，参数个数不符时编译报错，因此无需使用arguments机制。
 
**适配建议：**

请使用具体形参代替arguments对象获取参数。

**示例：**

**ArkTS1.1**
```typescript
function foo(u: string) {
  console.log(arguments[0]);
}

function bar(a: number, b?: number) {
  if (arguments.length === 1) {
    console.log("Only one argument passed");
  }
}

function sum() {
  let total = 0;
  for (let i = 0; i < arguments.length; i++) {
    total += arguments[i];
  }
  return total;
}

function test() {
  console.log(String(arguments.callee));
}
```

**ArkTS1.2**
```typescript
function foo(u: string) {
  console.log(u);
}

function bar(a: number, b?: number) {
  if (b === undefined) {
    console.log("Only one argument passed");
  }
}

function sum(...args: number[]) {  
  // 使用 `...rest` 替代 `arguments`
  return args.reduce((acc, num) => acc + num, 0);
}

function test() {
  console.log(test);  // 直接使用函数名
}
```

## 数组索引必须是整型数据

**规则：**`arkts-array-index-expr-type`

**规则解释：**

数组索引必须为整数类型。当索引由其他模块或第三方库传递时，迁移工具可能无法解析其类型，导致数组索引处报错。请开发者确认变量类型是否为整数，并决定如何修改代码。

**变更原因：**

为了实现数组更快的访问，ArkTS1.2支持数值类型的细化，并要求数组索引表达式必须是整数类型。
 
**适配建议：**

请将索引改为整数类型。

**示例：**

**ArkTS1.1**

```typescript
function foo (index: number) {
  let array = [1, 2, 3] 
  let element = array[index]
}

function getIndex(): number {
  return Math.random() * 10; // 可能返回小数
}

let array = [1, 2, 3];
for (let i: number = 0; i < array.length; i++) { // 违反规则
  console.log(array[i]);
}
```

**ArkTS1.2**

```typescript
function foo (index: int) {
  let array = [1, 2, 3] 
  let element = array[index]
}

function getIndex(): int {
  return Math.floor(Math.random() * 10);  // 转换为 `int`
}

let array = [1, 2, 3];
for (let i: int = 0; i < array.length; i++) { // 改为 `int`
  console.log(array[i]);
}
```

## 不支持通过负数访问数组

**规则：**`arkts-array-index-negative`

**规则解释：**

ArkTS1.2不支持使用负整数访问数组元素。当数组索引由其他模块或第三方库传递的变量决定时，这些变量的值需要在运行时确定。迁移工具无法判断索引值是否为负，因此会发出警报，请开发者确认索引值是否为负数，并进行相应修改。

**变更原因：**

在ArkTS1.1中，使用负数索引访问数组时，实际上是访问属性名为该负数的属性。如果数组不存在此属性，返回值为`undefined`。如果向负数索引写入值，实际上是为数组对象动态增加一个属性名为该负数的属性并赋值。ArkTS1.2是静态类型语言，无法动态为数组对象增加属性，因此不支持使用负数索引访问数组元素。

**适配建议：**

请使用非负整数来访问数组元素。

**示例：**

**ArkTS1.1**

```typescript
let an_array = [1, 2, 3];
let element = an_array [-1];
console.log(getElement(an_array, -1)); // 违反规则
for (let i: int = -1; i < an_array.length; i++) { // 违反规则
  console.log(an_array[i]);
}

function getElement(arr: number[], index: int) {
  return arr[index]; // 可能接收负数索引
}
```

**ArkTS1.2**

```typescript
let an_array = [1, 2, 3];
let element = an_array [1];
console.log(getElement(an_array, 1)); // 传递非负索引
for (let i: int = 0; i < an_array.length; i++) { // 仅允许非负索引
  console.log(an_array[i]);
}

function getElement(arr: number[], index: int) {
  if (index < 0) throw new Error("Index must be a non-negative integer");
  return arr[index]; // 仅允许非负整数
}
```

## 增加数组越界运行时检查

**规则：**`arkts-runtime-array-check`

**规则解释：**

ArkTS1.2会对数组索引的合法性进行运行时检查。请开发者自行确认索引的合法性，决定如何修改代码。

**变更原因：**

为了保证类型安全，ArkTS1.2在校验索引的合法性后访问数组元素。
 
**适配建议：**

在访问数组前，必须对索引值进行校验。

**示例：**

**ArkTS1.1**

```typescript
let a: number[] = []
a[100] = 5; // 可能越界
```

**ArkTS1.2**

```typescript
let a: number[] = []
if (100 < a.length) {
  a[100] = 5  // a[100]的值为5
}
```

## 元组和数组是两种不同类型

**规则：**`arkts-no-tuples-arrays`

**规则解释：**

ArkTS1.2中数组和元组是不同的类型。

**变更原因：**
 
ArkTS1.2中数组和元组是不同的类型。运行时使用元组类型可以获得更好的性能。

**适配建议：**

不要使用数组类型标注元组，而应正确使用对象类型。

**示例：**

**ArkTS1.1**

```typescript
const tuple: [number, number, boolean] = [1, 3.14, true];
const array: (number|boolean) [] = tuple;

const tuple: Array<number | boolean> = [1, 3.14, true];  // 违反规则

function getTuple(): (number | boolean)[] {  // 违反规则
  return [1, 3.14, true];
}
getTuple([1, 3.14, true]);  // 传入元组

type Point = (number | boolean)[];  // 违反规则
const p: Point = [3, 5, true];
```

**ArkTS1.2**

```typescript
const tuple: [number, number, boolean] = [1, 3.14, true];
const array:  [number, number, boolean] = tuple;

const tuple: [number, number, boolean] = [1, 3.14, true];  // 正确使用元组

function getTuple(): [number, number, boolean] {  // 正确使用元组
  return [1, 3.14, true];
}
getTuple([1, 3.14, true]);

type Point = [number, number, boolean];  // 使用元组
const p: Point = [3, 5, true];
```

## 函数类型转换及兼容原则

**规则：**`arkts-incompatible-function-types`

**规则解释：**

ArkTS1.2函数类型转换时，参数遵循[逆变](#逆变协变)规则，返回类型遵循[协变](#逆变协变)规则。

**变更原因：**
 
ArkTS1.1允许对函数类型的变量进行更宽松的赋值，而在ArkTS1.2中，将对函数类型的赋值进行更严格的检查。函数类型转换时，参数遵循[逆变](#逆变协变)规则，返回类型遵循[协变](#逆变协变)规则。

**适配建议：**

在外部包裹一层类型相同的箭头函数或者改为正确的类型。

**示例：**

**ArkTS1.1**

```typescript
type FuncType = (p: string) => void;
let f1: FuncType =
    (p: string): number => {
        return 0;
    }
let f2: FuncType = (p: any): void => {};
```

**ArkTS1.2**

```typescript
type FuncType = (p: string) => void;
let f1: FuncType =
  	(p: string) => {
        ((p: string): number => {
            return 0;
        })(p) 
    }
let f2: FuncType = (p: string): void => {};
```

## 不支持指数操作符

**规则：**`arkts-no-exponent-op`

**规则解释：**

ArkTS1.2不支持指数运算符（`**`和`**=`）。

**变更原因：**
 
ArkTS1.2不支持指数运算符（`**`和`**=`），采用语言基础库。

**适配建议：**

使用Math库中的pow方法来代替指数运算符。

**示例：**

**ArkTS1.1**

```typescript
let x = 2 ** 5;

let y = 3;
y **= 4; // 违反规则

let result = (1 + 2) ** (3 * 2); // 违反规则

function power(base: number, exponent: number) {
  return base ** exponent; // 违反规则
}

let values = [1, 2, 3];
let squared = values.map(v => v ** 2); // 违反规则
```

**ArkTS1.2**

```typescript
let x = Math.pow(2, 5);

let y = 3;
y = Math.pow(y, 4); // 直接使用 `Math.pow()`

let result = Math.pow(1 + 2, 3 * 2); // 直接使用 `Math.pow()`

function power(base: number, exponent: number) {
  return Math.pow(base, exponent); // 使用 `Math.pow()`
}

let values = [1, 2, 3];
let squared = values.map(v => Math.pow(v, 2)); // 使用 `Math.pow()`
```

## 不支持正则表达式字面量

**规则：**`arkts-no-regexp-literals`

**规则解释：**

ArkTS1.2不支持正则表达式字面量。

**变更原因：**
 
ArkTS1.2不支持正则表达式字面量。

**适配建议：**

使用RegExp类代替正则表达式字面量。

**示例：**

**ArkTS1.1**

```typescript
let regex: RegExp = /bc*d/;
let regex = /\d{2,4}-\w+/g; // 违反规则
function matchPattern(str: string) {
  return str.match(/hello\s+world/i); // 违反规则
}

let text = "Hello world!";
let result = text.replace(/world/, "ArkTS"); // 违反规则

let items = "apple,banana, cherry".split(/\s*,\s*/); // 违反规则
```

**ArkTS1.2**

```typescript
let regex: RegExp = new RegExp('bc*d');
let regex = new RegExp('\\d{2,4}-\\w+', 'g'); // 使用 `RegExp` 类
function matchPattern(str: string) {
  let regex = new RegExp('hello\\s+world', 'i'); // 使用 `RegExp`
  return str.match(regex);
}

let text = "Hello world!";
let regex = new RegExp('world'); // 使用 `RegExp` 类
let result = text.replace(regex, "ArkTS");

let regex = new RegExp('\\s*,\\s*'); // 使用 `RegExp`
let items = "apple,banana, cherry".split(regex);
```

## enum中当前语法不支持浮点数值

**规则：**`arkts-no-enum-mixed-types`

**规则解释：**

ArkTS1.2中enum当前语法不支持浮点数值。

**变更原因：**
 
enum表示一组离散的数据，使用浮点数据不符合设计理念，可能造成精度损失。因此，ArkTS1.2中enum的值必须为整型。

**适配建议：**

定义enum类型时，需显式声明number类型，以支持浮点数值。

**示例：**

**ArkTS1.1**

```typescript
enum Size {
  UP = 1.5,
  MIDDLE = 1,
  DOWN = 0.75
}
```

**ArkTS1.2**

```typescript
enum Size: number{ 
  UP = 1.5,
  MIDDLE = 1,
  DOWN = 0.75
}
```

## 不支持为函数增加属性

**规则：**`arkts-no-func-props`

**规则解释：**

ArkTS1.2不支持在函数上动态添加属性。

**变更原因：**
 
ArkTS1.2是静态类型语言，不支持在函数，方法上动态增加属性。

**适配建议：**

使用类来封装函数和属性。

**示例：**

**ArkTS1.1**

```typescript
function foo(path: string): void {
  console.log(path)
}
foo.baz = 1

const obj = {
  foo(path: string): void {
    console.log(path);
  }
};
obj.foo.baz = 2; // 违反规则

function createLogger() {
  function log(message: string) {
    console.log(message);
  }
  log.level = "debug"; // 违反规则
  return log;
}

const logger = createLogger();
console.log(logger.level);

function counter() {
  counter.count = (counter.count || 0) + 1; // 违反规则
  return counter.count;
}
console.log(counter());
```

**ArkTS1.2**

```typescript
class T {
  static foo(path: string): void {
    console.log(path)
  }
  static bar: number = 1
}

class T {
  static foo(path: string): void {
    console.log(path);
  }

  static baz: number = 2;
}
T.foo("example");
console.log(T.baz);

class Logger {
  static level = "debug";

  static log(message: string) {
    console.log(message);
  }
}
Logger.log("test");
console.log(Logger.level);

class Counter {
  static count = 0;

  static increment() {
    this.count += 1;
    return this.count;
  }
}
console.log(Counter.increment());
```

## 不支持TS装饰器

**规则：**`arkts-no-ts-decorators`

**规则解释：**

ArkTS1.2不支持通过自定义装饰器动态改变类、方法、属性或函数参数。

**变更原因：**
 
由于自定义装饰器需要动态改变类、方法、属性，而ArkTS1.2是静态类型语言，所以不支持自定义装饰器。

**适配建议：**

请参考以下示例修改代码。

**示例1：日志追踪装饰器**
```typescript
// ArkTS1.1代码：
// file1.ts
export function Log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.info(`[LOG] 方法 ${propertyKey} 被调用，参数: ${JSON.stringify(args)}`);
    const result = originalMethod.apply(this, args);
    console.info(`[LOG] 方法 ${propertyKey} 返回: ${result}`);
    return result;
  };
}
// file2.ets
import {Log} from './file1';
@Component
struct MyCounter {
  @State count: number = 0;

  @Log
  increment() {
    this.count++;
    return this.count;
  }

  build() {
    Button(`Count: ${this.count}`)
      .onClick(() => this.increment())
  }
}
```
```typescript
// ArkTS1.2代码：
import { Component, Button, ClickEvent } from '@ohos.arkui.component';
import { State } from '@ohos.arkui.stateManagement';

@Component
struct Counter {
  @State count: number = 0;

  increment() {
    console.info(`[LOG] 方法 increment 被调用，参数: []`);
    this.count++;
    const result = this.count;
    console.info(`[LOG] 方法 increment 返回: ${result}`);
    return result;
  }

  build() {
    Button(`Count: ${this.count}`)
      .onClick((e:ClickEvent) => {this.increment()})
  }
}
```
**示例2：防抖装饰器**
```typescript
// ArkTS1.1代码：
// file1.ts
export function Debounce(delay: number = 300) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    let timer: number = 0;
    const originalMethod = descriptor.value;
    descriptor.value = function (...args: any[]) {
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(() => {
        originalMethod.apply(this, args);
        timer = 0;
      }, delay);
    };
  };
}
// file2.ets
import {Debounce} from './file1';
@Component
struct SearchBox {
  @State keyword: string = '';

  @Debounce(500)
  onSearchInput(keyword: string) {
    this.keyword = keyword;
    console.info(`搜索: ${keyword}`);
    // 调用搜索API...
  }

  build() {
    TextField({ placeholder: '搜索...' })
      .onChange((value) => this.onSearchInput(value))
  }
}
```
```typescript
// ArkTS1.2代码：
import { Component, Button } from '@ohos.arkui.component';
import { State } from '@ohos.arkui.stateManagement';

@Component
struct SearchBox {
  @State keyword: string = '';
  private debounceTimer: Int = 0;

  onSearchInput(keyword: string) {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.keyword = keyword;
      console.info(`搜索: ${keyword}`);
      // 调用搜索API...
    }, 500);
  }

  build() {
    // TextField({ placeholder: '搜索...' })
    //   .onChange((value) => {this.onSearchInput(value)})
  }
}
```
**示例3：权限校验装饰器**
```typescript
// ArkTS1.1代码：
// file1.ts
export function RequiresPermission(permission: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args: any[]) {
      if (checkUserPermission(permission)) {  // 自定义权限检查函数
        return originalMethod.apply(this, args);
      } else {
        console.error(`[权限不足] 需要 ${permission} 权限`);
        return null;
      }
    };
  };
}
// file2.ets
import {RequiresPermission} from './file1';

@Component
struct AdminPanel {
  @RequiresPermission('admin')
  deleteUser(userId: string) {
    // 删除用户逻辑...
  }

  build() {
    Button('删除用户')
      .onClick(() => this.deleteUser('123'))
  }
}
```
```typescript
// ArkTS1.2代码：
import { Component, Button, ClickEvent } from '@ohos.arkui.component';
import { State } from '@ohos.arkui.stateManagement';

@Component
struct AdminPanel {
  deleteUser(userId: string) {
    if (!checkUserPermission('admin')) {  // 自定义权限检查函数
      console.error(`[权限不足] 需要 admin 权限`);
      return;
    }
    // 删除用户逻辑...
  }

  build() {
    Button('删除用户')
      .onClick((e:ClickEvent) => {this.deleteUser('123')})
  }
}
```
**示例4：性能监控装饰器**
```typescript
// ArkTS1.1代码：
// file1.ts
export function PerformanceMonitor(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;
  descriptor.value = function (...args: any[]) {
    const start = Date.now();
    const result = originalMethod.apply(this, args);
    const end = Date.now();
    console.info(`[性能] 方法 ${propertyKey} 执行耗时: ${end - start}ms`);
    return result;
  };
}
// file2.ets
import {PerformanceMonitor} from './file1';

@Component
struct DataLoader {
  @PerformanceMonitor
  loadLargeData() {
    // 模拟耗时操作
    let sum = 0;
    for (let i = 0; i < 1000000; i++) {
      sum += i;
    }
    return sum;
  }

  build() {
    Button('加载数据')
      .onClick(() => this.loadLargeData())
  }
}
```
```typescript
// ArkTS1.2代码：
import { Component, Button, ClickEvent } from '@ohos.arkui.component';
import { State } from '@ohos.arkui.stateManagement';
@Component
struct DataLoader {
  loadLargeData() {
    const start = Date.now();
    // 模拟耗时操作
    let sum = 0;
    for (let i = 0; i < 1000000; i++) {
      sum += i;
    }
    const end = Date.now();
    console.info(`[性能] 方法 loadLargeData 执行耗时: ${end - start}ms`);
    return sum;
  }

  build() {
    Button('加载数据')
      .onClick((e:ClickEvent) => {this.loadLargeData()})
  }
}
```
**示例5：自动保存装饰器**
```typescript
// ArkTS1.1代码：
// file1.ts
export function AutoSave(key: string) {
  return function (target: any, propertyKey: string) {
    let value = target[propertyKey];
    
    const getter = () => value;
    const setter = (newVal: any) => {
      value = newVal;
      try {
        console.info(`[自动保存] 键: ${key}, 值: ${JSON.stringify(newVal)}`);
        localStorage.setItem(key, JSON.stringify(newVal));  // 实际项目需使用存储API
      } catch (e) {
        console.error(`[自动保存失败] ${e}`);
      }
    };
    
    Object.defineProperty(target, propertyKey, {
      get: getter,
      set: setter,
      enumerable: true,
      configurable: true
    });
  };
}
// file2.ets
import {AutoSave} from './file1';
@Component
struct Settings {
  @AutoSave('user_settings')
  theme: string = 'light';

  build() {
    Row() {
      Button('切换主题')
        .onClick(() => this.theme = this.theme === 'light' ? 'dark' : 'light')
    }
  }
}
```
```typescript
// ArkTS1.2代码：
import { Component, Button, ClickEvent,Row } from '@ohos.arkui.component';
import { State } from '@ohos.arkui.stateManagement';

@Component
struct Settings {
  @State theme: string = 'light';

  setTheme(newTheme: string) {
    this.theme = newTheme;
    try {
      console.info(`[自动保存] 键: user_settings, 值: ${JSON.stringify(newTheme)}`);
      localStorage.setItem('user_settings', JSON.stringify(newTheme));  // 实际项目需使用存储API
    } catch (e) {
      console.error(`[自动保存失败] ${e}`);
    }
  }

  build() {
    Row() {
      Button('切换主题')
        .onClick((e:ClickEvent) => {this.setTheme(this.theme === 'light' ? 'dark' : 'light')})
    }
  }
}
```

## 属性和方法不能交叉重写

**规则：**`arkts-no-method-overriding-field`

**规则解释：**

在ArkTS1.2中，子类继承父类或实现接口时，属性和方法不能交叉重写，即方法不能重写属性，属性不能重写方法。

**变更原因：**
 
ArkTS1.1是动态类型语言，类的属性和方法本质上都是对象，因此在继承或实现时，方法和属性可以交叉重写。但是ArkTS1.2是静态类型语言，方法和属性不能交叉重写。

**适配建议：**

明确区分方法和属性，不要交叉重写。统一方法的声明方式。

**示例：**

**ArkTS1.1**

```typescript
interface Person {
  cb: () => void
}

class student implements Person{
  cb() {}
} 

interface Transformer<T> {
  transform: (value: T) => T; // 违反规则
}

class StringTransformer implements Transformer<string> {
  transform(value: string) { return value.toUpperCase(); }  // 违反规则
}
```

**ArkTS1.2**

```typescript
interface Person {
  cb(): void
}

class student implements Person{
  cb() {}
}

interface Transformer<T> {
  transform(value: T): T;  // 变成方法
}

class StringTransformer implements Transformer<string> {
  transform(value: string) { return value.toUpperCase(); }  // 正确
}
```

## 限定switch语句中case语句类型

**规则：**`arkts-switch-expr`

**规则解释：**

ArkTS1.2的switch表达式类型只能为number、string、enum。

**变更原因：**
 
提高代码可读性和执行性能。

**适配建议：**

使用number、string、enum作为switch表达式类型。

**示例：**

**ArkTS1.1**

```typescript
const isTrue = true;
switch (isTrue) {
    case true: // 违反规则
        console.log('It\'s true'); break;
    case false:  // 违反规则
        console.log('It\'s false'); break;
}

const obj = { value: 1 };
switch (obj) {  // 违反规则
    case { value: 1 }:
        console.log('Matched'); break;
}

const arr = [1, 2, 3];
switch (arr) {  // 违反规则
    case [1, 2, 3]: 
        console.log('Matched'); break;
}
```

**ArkTS1.2**

```typescript
const isTrue = 'true';
switch (isTrue) {
    case 'true': 
        console.log('It\'s true'); break;
    case 'false': 
        console.log('It\'s false'); break;
}

const objValue = 1;  // 仅存储值
switch (objValue) {
    case 1:
        console.log('Matched'); break;
}

const arrValue = '1,2,3';  // 变成字符串
switch (arrValue) {
    case '1,2,3':
        console.log('Matched'); break;
}
```

## 不支持重复case语句

**规则：**`arkts-case-expr`

**规则解释：**

ArkTS1.2不支持Switch语句的中case重复。

**变更原因：**
 
提高代码的可读性。

**适配建议：**

避免出现重复的case。

**示例：**

**ArkTS1.1**

```typescript
const num = 1;
switch (num) {
    case 1:
        console.log('First match');
    case 1:
        console.log('Second match');
        break;
    default:
        console.log('No match');
}

enum Status {
    Active,
    Inactive
}

const state = Status.Active;
switch (state) {
    case Status.Active:
        console.log('User is active');
        break;
    case Status.Active: // 违反规则
        console.log('Already active');
        break;
}
```

**ArkTS1.2**

```typescript
const num = 1;
switch (num) {
    case 1:
        console.log('First match');
        console.log('Second match');
        break;
    default:
        console.log('No match');
}

switch (state) {
    case Status.Active:
        console.log('User is active');
        console.log('Already active'); // 代码合并
        break;
}
```

## 不支持lazy关键字

**规则：**`arkts-no-lazy-import`

**规则解释：**

ArkTS1.2不需要lazy关键字。

**变更原因：**
 
ArkTS1.2默认支持懒加载，无需使用lazy关键字。

**适配建议：**

移除lazy关键字。

**示例：**

**ArkTS1.1**

```typescript
// file1.ets
let a='a';
let b='b';
let c='c';
export {a,b,c};

// file2.ets
import lazy { a } from './file1';
import lazy { b, c } from './file1'; // 违反规则
```

**ArkTS1.2**

```typescript
// file1.ets
let a='a';
let b='b';
let c='c';
export {a,b,c};

// file2.ets
import { a } from './file1';
import { b, c } from './file1'; // 移除lazy
```

## 不支持动态import

**规则：**`arkts-no-dynamic-import`

**规则解释：**

在ArkTS1.2中，不支持动态import。

**变更原因：**
 
ArkTS1.2中模块加载默认支持懒加载，无需动态import。

**适配建议：**

将动态import改为静态import。

**示例：**

**ArkTS1.1**

```typescript
// file1.ets
export const a = 'file1';
// file2.ets
import('./file1').then((m) => { // 在ArkTS1.2中动态import是不支持的
  console.log('success');
})
async () => {
  const module = await import('./file1'); // 在ArkTS1.2中动态import是不支持的
}
```

**ArkTS1.2**

```typescript
// file1.ets
export const a = 'file1';
// file2.ets
import {a} from './file1'  // 支持静态import
```

## 不支持副作用导入

**规则：**`arkts-no-side-effect-import`

**规则解释：**

ArkTS1.2不支持副作用导入的功能。

**变更原因：**
 
ArkTS1.2中模块加载支持懒加载，不支持副作用导入的功能。

**适配建议：**

将导入文件中的执行逻辑移到本文件中。

**示例：**

**ArkTS1.1**

```typescript
// logger.ets
console.log("Logger initialized!");

// main.ets
import "./logger";
console.log("Main program running...");
```

**ArkTS1.2**

```typescript
// main.ets
console.log("Logger initialized!");
console.log("Main program running...");
```

## 不支持globalThis

**规则：**`arkts-no-globalthis`

**规则解释：**

ArkTS1.2不支持globalThis。

**变更原因：**
 
ArkTS1.2不支持动态更改对象布局，因此不支持全局作用域和globalThis。

**适配建议：**

按示例修改。

**示例：**

**ArkTS1.1**

```typescript
// 全局文件中
var abc = 100;

// 从上面引用'abc'
let x = globalThis.abc;
```

**ArkTS1.2**

```typescript
// file1
export let abc: number = 100;

// file2
import * as M from 'file1'

let x = M.abc;
```

## 不支持Function.bind方法

**规则：**`arkts-no-func-bind`

**规则解释：**

ArkTS1.2不支持标准库函数Function.bind。

**变更原因：**
 
ArkTS1.2中的方法会自动捕获上下文中的`this`，因此无需使用`Function.bind`显式绑定`this`。

**适配建议：**

使用“=”（等号）将函数赋值给变量。

**示例：**

**ArkTS1.1**

```typescript
class MyClass {
  constructor(public name: string) {}

  greet() {
    console.log(`Hello, my name is ${this.name}`);
  }
}

const instance = new MyClass("Alice");
const boundGreet = instance.greet.bind(instance); // 违反规则，不允许使用 Function.bind
boundGreet();
```

**ArkTS1.2**

```typescript
class MyClass {
    name: string;
    constructor(name: string) { this.name = name; }
    greet() {
        console.log(`Hello, my name is ${this.name}`);
    }
}

const instance = new MyClass("Alice");
const boundGreet = () => instance.greet(); // 使用箭头函数
boundGreet(); // Hello, my name is Alice
```

## 不支持将类作为对象

**规则：**`arkts-no-classes-as-obj`

**规则解释：**

在ArkTS1.2中，不支持将class用作对象。

**变更原因：**
 
在ArkTS1.2中，class声明的是一个新的类型，而不是一个值。因此，不支持将class用作对象，例如赋值给变量。

**适配建议：**

通过反射来实现。

**示例：**

**ArkTS1.1**

```typescript
class MyClass {
  constructor(public name: string) {}
}

let obj = MyClass; // 违反规则
```

**ArkTS1.2**

```typescript
class MyClass {
  constructor(name: string) {}
}

// 需要通过反射来实现
let className = "path.to.MyClass";
let linker = Class.ofCaller()!.getLinker();
let classType: ClassType | undefined = linker.getType(className) as ClassType;
```

## arkts-limited-stdlib

**规则：**`arkts-limited-stdlib`

**规则解释：**

ArkTS1.2中禁止使用以下接口：

- 全局对象的属性和方法：`eval`

- Object： `__proto__`、`__defineGetter__`、`__defineSetter__`、`__lookupGetter__`、`__lookupSetter__`、`assign`、`create`、`defineProperties`、`defineProperty`、`freeze`、`fromEntries`、`getOwnPropertyDescriptor`、`getOwnPropertyDescriptors`、`getOwnPropertySymbols`、`getPrototypeOf`、`hasOwnProperty`、`is`、`isExtensible`、`isFrozen`、`isPrototypeOf`、`isSealed`、`preventExtensions`、`propertyIsEnumerable`、`seal`、`setPrototypeOf`

- Reflect：`apply`、`construct`、`defineProperty`、`deleteProperty`、`getOwnPropertyDescriptor`、`getPrototypeOf`、`isExtensible`、`preventExtensions`、`setPrototypeOf`

- Proxy：`handler.apply()`、`handler.construct()`、`handler.defineProperty()`、`handler.deleteProperty()`、`handler.get()`、`handler.getOwnPropertyDescriptor()`、`handler.getPrototypeOf()`、`handler.has()`、`handler.isExtensible()`、`handler.ownKeys()`、`handler.preventExtensions()`、`handler.set()`、`handler.setPrototypeOf()`

**变更原因：**
 
ArkTS1.2不允许使用TypeScript或JavaScript标准库中的这些接口，这些接口大多与动态特性相关。

**适配建议：**

NA

## 不支持structural typing

**规则：**`arkts-no-structural-typing`

**规则解释：**
 
ArkTS1.2不支持structural typing。

**变更原因：**
 
支持structural typing是重要特性，需在语言规范、编译器和运行时充分考虑并仔细实现。ArkTS 1.2使用静态类型，为支持此特性，运行时会增加额外性能开销。

**适配建议：**

使用其他机制，例如继承、接口或类型别名。

**示例：**

**ArkTS1.1**

```typescript
// case1
class A {
  v: number = 0
}

class B {
  v: number = 0
}

let a = new B() as A

// case2
class C<T> {
  u: T
}

let b: C<B> = new C<A>()

// case3
class A {
  u: number = 0
}

class B {
  u: number = 0
}

(): A => { return new B() }

class A {
  v: number = 0
}

class B {
  v: number = 0
}
class C<T> {
  u: T;
}

let b: C<B> = new C<A>(); // 违反规则
```

**ArkTS1.2**

```typescript
// case1
class A {
  v: number = 0
}

class B {
  v: number = 0
}

let a = new B()

// case2
class C<T> {
  u: T
}

let b: C<A> = new C<A>()

// case3
class A {
  u: number = 0
}

class B {
  u: number = 0
}

(): B => { return new B() }

class A {
  v: number = 0
}

class B {
  v: number = 0
}
let b: C<A> = new C<A>(); // 使用相同的泛型类型

```

## 禁止extends/implements表达式

**规则：**`arkts-no-extends-expression`

**规则解释：**

ArkTS1.2禁止extends/implements表达式。

**变更原因：**
 
ArkTS1.2中规范了类的继承规则：类不能作为对象使用，且在继承时无法继承表达式。

**适配建议：**

直接使用class的类型。

**示例：**

**ArkTS1.1**

```typescript
class A {
  v: number = 0
}

let a = A;

class B extends a { // 违反规则
  u: number = 0
}

function getBase() {
  return class {
    w: number = 0;
  };
}

class B extends getBase() { // 违反规则
  u: number = 0;
}

interface I {
  w: number;
}

let i = I;

class B implements i { // 违反规则
  w: number = 0;
}

class A {
  v: number = 0;
}

class B extends new A() { // 违反规则
  u: number = 0;
}
```

**ArkTS1.2**

```typescript
class A {
  v: number = 0
}

class B extends A { // 直接继承类
  u: number = 0
}

class Base {
  w: number = 0;
}

class B extends Base { // 直接继承类
  u: number = 0;
}

interface I {
  w: number;
}

class B implements I { // 直接使用接口
  w: number = 0;
}

class A {
  v: number = 0;
}

class B extends A { // 直接继承类
  u: number = 0;
}
```

## 不支持类TS重载

**规则：**`arkts-no-ts-overload`

**规则解释：**

ArkTS1.2不支持TS-like的重载。

**变更原因：**
 
重载时使用不同的函数体可以提高执行效率。

**适配建议：**

重载时分别使用不同的函数体。

**示例：**

**ArkTS1.1**

```typescript
function foo(): void
function foo(x: string): void
function foo(x?: string): void { // 违反规则
  /*body*/
}

function sum(x: number, y: number): number;
function sum(x: number, y: number, z: number): number;
function sum(x: number, y: number, z?: number): number {  // 违反规则
  return z ? x + y + z : x + y;
}

function foo(): string;
function foo(x: number): number;
function foo(x?: number): string | number {  // 违反规则
  return x !== undefined ? x * 2 : "default";
}
```

**ArkTS1.2**

```typescript
function foo(x?: string): void {
  /*body*/
}

function sumTwo(x: number, y: number): number {  // 独立实现
  return x + y;
}

function sumThree(x: number, y: number, z: number): number {  // 独立实现
  return x + y + z;
}

function fooString(): string {  // 独立实现
  return "default";
}

function fooNumber(x: number): number {  // 独立实现
  return x * 2;
}
```

## enum/class/interface的属性/方法名称须使用合法标识符

**规则：**`arkts-identifiers-as-prop-names`

**规则解释：**

ArkTS1.2不支持将字符串作为class、interface、enum等属性或元素的名称，仅支持合法标识符作为属性。

**变更原因：**
 
在ArkTS1.2中，为了增强对边界场景的约束，对象的属性名不能使用数字或字符串。

**适配建议：**

将属性名从字符串改为标识符。

**示例：**

**ArkTS1.1**

```typescript
enum A{
 'red' = '1'
}
```

**ArkTS1.2**

```typescript
enum A{
  red = '1'
}
```

## 创建泛型实例需要类型实参

**规则：**`arkts-no-inferred-generic-params`

**规则解释：**

ArkTS1.2中，创建泛型实例时需要指定类型实参。

**变更原因：**
 
ArkTS1.2遵循空安全，未指定泛型类型实参时，创建实例时无法明确元素或属性类型。

**适配建议：**

创建泛型实例时指定类型实参。

**示例：**

**ArkTS1.1**

```typescript
new Array() // 违反规则

new Map(); // 违反规则

class Box<T> {
  value: T;
  constructor(value: T) {
    this.value = value;
  }
}

let box = new Box(42); // 违反规则
```

**ArkTS1.2**

```typescript
new Array<SomeType>() // 指定类型

new Map<string, number>(); // 显式指定键值类型

let box = new Box<number>(42); // 明确指定类型
```

## 不支持[]访问对象属性

**规则：**`arkts-no-props-by-index`

**规则解释：**

不能使用[]的方式动态访问object类型对象的属性。

**变更原因：**
 
在ArkTS1.2中，对象结构在编译时已确定。为避免运行时错误并提升性能，不能使用[]方式动态访问object类型对象的属性。

**适配建议：**

使用点访问符代替[]。

**示例：**

**ArkTS1.1**

```typescript
function foo(u: object) {
  u['key'] // 违反规则
}

const person = { name: "Alice", age: 30 };
console.log(person['name']); // 违反规则

const data = JSON.parse('{ "name": "Alice" }');
console.log(data['name']); // 违反规则
```

**ArkTS1.2**

```typescript
function foo(m: Map<string, Object>) {
    m.get('key') // 使用 `Map`
}

interface Person {
    name: string;
    age: number;
}
const person: Person = {name: 'John',age: 30};
console.log(person.name); // 直接使用 `.` 访问

class UserData {
    name?: string;
}
const data =  JSON.parse<UserData>('{ "name": "Alice" }', Type.from<UserData>())!;
console.log(data.name); // 直接使用点访问符
```

## 对象字面量只包含属性不包含方法

**规则：**`arkts-obj-literal-props`

**规则解释：**

ArkTS1.2中不支持在对象字面量中定义方法。

**变更原因：**
 
静态语言中，类的方法被所有实例共享，无法通过对象字面量重新定义。

**适配建议：**

使用属性赋值方式。

**示例：**

**ArkTS1.1**

```typescript
class A {
  foo: () => void = () => {}
}

let a: A = {
  foo() { // 违反规则
    console.log('hello')
  }
}

interface Person {
  sayHello: () => void;
}

let p: Person = {
  sayHello() {  // 违反规则，方法定义方式错误
    console.log('Hi');
  }
};

type Handler = {
  foo(): void; 
};

let handler: Handler = {
  foo() {  // 违反规则
    console.log("Executing handler");
  }
};
```

**ArkTS1.2**

```typescript
class A {
  foo : () => void = () => {}
}

let a: A = {
  foo: () => {
    console.log('hello')
  }
}

interface Person {
  sayHello: () => void;
}

let p: Person = {
  sayHello: () => {  // 使用属性赋值方式
    console.log('Hi');
  }
};

type Handler = A;

let handler: Handler = {
  foo: () => {  // 修正方法定义方式
    console.log("Executing handler");
  }
};
```

## 对象字面量生成类的实例

**规则：**`arkts-obj-literal-generate-class-instance`

**规则解释：**

ArkTS1.2中，对象字面量会生成类的实例。

**变更原因：**
 
ArkTS1.2是静态类型语言，所有的对象都要有对应的类型，因此对象字面量也要生成对应类的实例。

**适配建议：**

不涉及。

**示例：**

**ArkTS1.1**

```typescript
class A {
  v: number = 0
}

let a: A = { v: 123 }
console.log('output:'+(a instanceof A));  // 输出：false

class B {
  v: number = 0;
  hello() {
    return "Hello";
  }
}

let b: B = { v: 123 };
console.log(b.hello()); // 报错，没有hello方法

class C {
  v: number = 0;
}

let c: C = { v: 123 };
console.log('output:'+(c instanceof C)); // 输出：false
```

**ArkTS1.2**

```typescript
class A {
    v: number = 0
}

let a: A = { v: 123 }
console.log(a instanceof A)  //  输出：true

class B {
    v: number = 0;
    hello() {
        return "Hello";
    }
}

let b: B = { v: 123 };
console.log(b.hello()); // 输出：Hello

class C {
    v: number = 0;
}

let c: C = { v: 123 };
console.log(c instanceof C); // 输出：true

```

## 增强对联合类型属性访问的编译时检查

**规则：**`arkts-common-union-member-access`

**规则解释：**

ArkTS1.2在编译时会对联合类型的同名属性进行编译检查，要求同名属性具有相同的类型。

**变更原因：**

在ArkTS1.2中，对象的结构在编译时确定。为了避免运行时错误，ArkTS1.2在编译时会检查联合类型的同名属性，确保它们具有相同的类型。

**适配建议：**

避免使用联合类型。在使用联合类型时，可以通过as、重载等方式实现单一类型机制。

**示例：**

**ArkTS1.1**

```typescript
class A {
  v: number = 1
}

class B {
  u: string = ''
}

function foo(a: A | B) {
  console.log(a.v) // 违反规则
  console.log(a.u) // 违反规则
}
```

**ArkTS1.2**

```typescript
class A {
  v: number = 1
}

class B {
  u: string = ''
}

function foo(a: A) {
  console.log(a.v)
}

function foo(a: B) {
  console.log(a.u)
}
```

## 类的静态属性需要有初始值

**规则：**`arkts-class-static-initialization`

**规则解释：**

在ArkTS1.2中，为了遵循null-safety（空安全），需要为属性赋上初始值。

**变更原因：**

ArkTS1.2遵循null-safety（空安全），需要为类的静态属性赋初始值（具有默认值的类型除外）。

**适配建议：**

为静态属性赋初始值。

**示例：**

**ArkTS1.1**

```typescript
class B {}

class A {
  static b: B
}

class A {
  static count: number; // 违反规则，必须初始化
}

class A {
  static config: { theme: string }; // 违反规则，必须初始化
}

class A {
  static name: string;

  constructor() {
    A.name = "default"; // 违反规则，静态属性必须在定义时初始化
  }
}
```

**ArkTS1.2**

```typescript
class B {}

class A {
  static b? : B
  static b: B | undefined = undefined
}

class A {
  static count: number = 0; // 提供初始值
}

class A {
  static config: { theme: string } = { theme: "light" }; // 提供初始值
}

class A {
  static name: string = "default"; // 在定义时初始化
}

```

## 不支持TS-like `Function`类型的调用方式

**规则：**`arkts-no-ts-like-function-call`

**规则解释：**

ArkTS1.2中不支持TS-like`Function`类型。

**变更原因：**

ArkTS1.2对函数类型进行更严格的编译器检查。函数返回类型需要严格定义来保证类型安全，因此不支持TS-like`Function`类型。

**适配建议：**

使用func.unsafeCall()代替func()。

**示例：**

**ArkTS1.1**

```typescript
let f: Function = () => {} // 违反规则

function run(fn: Function) {  // 违反规则
  fn();
}

let fn: Function = (x: number) => x + 1; // 违反规则

class A {
  func: Function = () => {}; // 违反规则
}

function getFunction(): Function { // 违反规则
  return () => {};
}
```

**ArkTS1.2**

```typescript
type F<R> = () => R;
type F1<P, R> = (p:  P) => R

let f: F<void> = () => {}

function run(fn: () => void) {  // 指定返回类型
  fn();
}

let fn: (x: number) => number = (x) => x + 1; // 明确参数类型

class A {
  func: () => void = () => {}; // 明确类型
}

function getFunction(): () => void { // 明确返回类型
  return () => {};
}
```

## 不支持可选方法

**规则：**`arkts-optional-methods`

**规则解释：**

ArkTS1.2不支持类中的可选方法。

**变更原因：**

ArkTS1.2中，类的方法由所有实例共享。增加可选方法支持会增加开发者判断空值的成本，影响性能。

**适配建议：**

用可选属性代替可选方法。

**示例：**

**ArkTS1.1**

```typescript
interface InterfaceA {
  aboutToDisappear?(): void
}
class ClassA {
  aboutToDisappear?(): void {}
}
```

**ArkTS1.2**

```typescript
interface InterfaceA {
  aboutToDisappear?: () => void
}
class ClassA {
  aboutToDisappear?: () => void = () => {}
}
```

## 实例方法当作对象时会绑定this

**规则：**`arkts-instance-method-bind-this`

**规则解释：**

在ArkTS1.2中，实例方法当作对象时会绑定上下文中的`this`。

**变更原因：**

在ArkTS1.1中，`this`的指向取决于函数的调用方式。示例中，当`a.foo1`被赋值给变量后，变成了一个独立函数，调用时不再与`a`实例关联，导致方法中的`this`指向`undefined`。可以使用`a.foo2`的箭头函数来解决这个问题。箭头函数在类中作为方法定义时，会捕获类实例的上下文，确保`this`始终指向实例。

ArkTS1.2中则不存在这个问题，实例方法和箭头函数都会捕获上下文中的`this`。

**适配建议：**

不涉及。

**示例：**

**ArkTS1.1**

```typescript
class A {
  n: string = 'a'
  foo1() { console.log (this) }
  foo2 = () => { console.log(this.n) }
}

let a = new A();
const foo1 = a.foo1;
const foo2 = a.foo2;
foo1() // 输出: 'undefined'
foo2() // 输出: 'a'
```

**ArkTS1.2**

```typescript
class A {
  n: string = 'a'
  foo() { console.log (this.n) }
}
let a = new A()
const method = a.foo
method()   // 输出: 'a'
```

## namespace内方法不能重名

**规则：**`arkts-no-duplicate-function-name`

**规则解释：**

在ArkTS1.2中，相同namespace中的方法不能重名。

**变更原因：**

由于ArkTS1.2中会将名称相同的namespace合并成一个namespace，同名方法会导致冲突。

**适配建议：**

相同namespace中的方法不能重名。

**示例：**

**ArkTS1.1**

```typescript
namespace A {
  export function foo() {  // 错误：命名空间 'A' 中重复导出函数 'foo'
    console.log('test1');
  }
}

namespace A {
  export function foo() {  // 错误：命名空间 'A' 中重复导出函数 'foo'
    console.log('test2');
  }
}

```

**ArkTS1.2**

```typescript
namespace A {
  export function foo1() {  // 修改函数名称，避免命名冲突
    console.log('test1');
  }
}

namespace A {
  export function foo2() {
    console.log('test2');
  }
}
```

## 不支持在constructor中声明字段

**规则：**`arkts-no-ctor-prop-decls`

**规则解释：**

ArkTS1.2不支持在constructor中声明类字段。

**变更原因：**

ArkTS1.2在编译期确定类型布局，运行期不允许修改，以提高性能。

**适配建议：**

改为在class中声明字段。

**示例：**

**ArkTS1.1**

```typescript
class A {
  constructor(readonly a: string) {
  }
}

class Base {
  readonly b: string = "base";
}

class A extends Base {
  constructor(override readonly b: string) {  // 违反规则
    super();
  }
}
```

**ArkTS1.2**

```typescript
class A {
  readonly a: string
  constructor(a: string) {
    this.a = a
  }
}

class Base {
  readonly b: string = "base";
}

class A extends Base {
  override readonly b: string;  // 显式声明字段
  constructor(b: string) {
    super();
    this.b = b;
  }
}

```

## 不支持tagged templates

**规则：**`arkts-no-tagged-templates`

**规则解释：**

ArkTS1.2不支持Tagged templates（标签模板字符串）。

**变更原因：**

ArkTS1.2规范函数调用方式，支持字符串相加，但不支持Tagged templates（标签模板字符串）。

**适配建议：**

改为函数调用和字符串加法。

**示例：**

**ArkTS1.1**

```typescript
function myTag(strings: TemplateStringsArray, value: string): string {
    return strings[0] + value.toUpperCase() + strings[1];
}

const name = 'john';
const result = myTag`Hello, ${name}!`;
console.log(result);

function formatTag(strings: TemplateStringsArray, first: string, last: string): string {  
    return `${strings[0]}${first.toUpperCase()} ${last.toUpperCase()}${strings[1]}`;
}

const firstName = 'john';
const lastName = 'doe';
const result = formatTag`Hello, ${firstName} ${lastName}!`;  // 违反规则
console.log(result);
```

**ArkTS1.2**

```typescript
function myTagWithoutTemplate(strings: string, value: string): string {
    return strings + value.toUpperCase();
}

const name = 'john';

const part1 = 'Hello, ';
const part2 = '!';
const result = myTagWithoutTemplate(part1, name) + part2;
console.log(result);

function formatWithoutTemplate(greeting: string, first: string, last: string, end: string): string {  
    return greeting + first.toUpperCase() + ' ' + last.toUpperCase() + end;
}

const firstName = 'john';
const lastName = 'doe';
const result = formatWithoutTemplate('Hello, ', firstName, lastName, '!');  // 直接使用函数参数
console.log(result);
```

## 不支持确定赋值断言

**规则：**`arkts-no-definite-assignment`

**规则解释：**

ArkTS1.2不支持确定赋值断言，例如：let v!: T。

**变更原因：**

ArkTS1.2语法层面不支持。

**适配建议：**

修改声明方式。

**示例：**

**ArkTS1.1**

```typescript
let x!: number // 提示：在使用前将x初始化

initialize();

function initialize() {
  x = 10;
}

console.log('x = ' + x);
```

**ArkTS1.2**

```typescript
function initialize(): number {
  return 10;
}

let x: number = initialize();

console.log('x = ' + x);
```

## Record增加运行时类型

**规则：**`arkts-record-add-runtime-type`

**规则解释：**

在ArkTS1.1中，Record是一个编译时类型，而不是一个运行时构造函数或类。

在ArkTS1.2中，Record对象具有运行时类型。

**变更理由：**

在ArkTS1.2中，对象字面量会生成类的实例。

**适配建议：**

开发者需要将点访问符改为[]访问符。

**示例：**

**ArkTS1.1**

```typescript
  let a: Record<string, number> = { 'v': 123 };
  console.log(String(a instanceof Record)) // error
  console.log(a['v'] + '') // 输出：123
  console.log(a.v + '') // 输出：123
```

**ArkTS1.2**

```typescript
let a: Record<string, number> = { 'v': 123 };
console.log(String(a instanceof Record)) // 输出：true
console.log(a['v'] + '') // 输出：123
console.log(a.v + '') // error
```

## as具有运行时语义

**规则：**`arkts-no-ts-like-as`

**规则解释：**

ArkTS1.2中`as`具有运行时语义。

**变更理由：**

ArkTS1.1中的`as`只在编译时提供类型信息，如果类型断言失败，报错时机取决于后续的代码操作。

ArkTS1.2中的`as`会在运行时进行类型检查和可能的类型转换，如果类型断言失败，会立即抛出错误。

**适配建议：**

修改异常处理逻辑。

**示例：**

**ArkTS1.1**

```typescript
// ArkTS1.1
interface I {}
class A implements I {
  m: number = 0;
}

class B implements I {
  n: string = 'a';
}

let a: A = new A();
let i: I = a;
let t: B = i as B; // ArkTS1.1：正常编译运行，ArkTS1.2：运行时异常
t.n.toString();    // ArkTS1.1：运行时崩溃
```

**ArkTS1.2**

```typescript
// ArkTS1.2
interface I {}
class A implements I {
    m: number = 0;
}

class B implements I {
    n: string = 'a';
}

let a: A = new A();
let i: I = a;
let t: B = i as B; // ArkTS1.2：运行时异常
t.n.toString();
```

## catch语句中是error类型

**规则：**`arkts-no-ts-like-catch-type`

**规则解释：**

在ArkTS1.2的静态模式中，类型必须明确，同时需考虑与ArkTS1.1的兼容性。对于catch(e)的语法，默认e为Error类型。

**变更理由：**

在ArkTS1.1上catch语句中的e是any类型。编译器不会对catch语句中的异常进行编译时类型检查。当ArkTS1.1上限制throw时，只能抛出Error类型。

在ArkTS1.2中，类型必须明确。对于catch(e)的语法，默认e为Error类型，以保持与ArkTS1.1的兼容性。

**适配建议：**

开发者需要将catch(e)转换成需要处理的异常类型，例如：`(e as SomeError).prop`。

**示例：**

**ArkTS1.1**

```typescript
try {
  throw new Error();
} catch(e) {  // e是any类型
  e.message; // ArkTS1.1编译通过，运行正常
  e.prop;     // ArkTS1.1编译通过，输出undefined
}
```

**ArkTS1.2**

```typescript
try {
  throw new Error();
} catch(e:Error) {  // e是Error类型
  e.message;   // ArkTS1.2编译通过，运行正常
  e.prop;      // ArkTS1.2编译错误，需要将e转换成需要处理的异常类型，例如：(e as SomeError).prop
}
```

## 不支持逻辑赋值运算

**规则：**`arkts-unsupport-operator`

**规则解释：**

ArkTS1.2暂不支持`&&=`、`||=`、`??=`这三种逻辑赋值运算符。

**变更理由：**

语言层面暂不支持`&&=`、`||=`、`??=`，但是支持`&=`、`|=`、`?=`这类逻辑赋值运算符。

**适配建议：**
 
开发者自行替换为运算后赋值的写法，如：`x &&= y`替换为`x = x && y`。

**示例：**

**ArkTS1.1**

```typescript
let a = 1;
a &&= 2;    // 结果: 2，ArkTS1.2暂不支持
a ||= 3;   // 结果: 2，ArkTS1.2暂不支持
a ??= 4;  // 结果: 2，ArkTS1.2暂不支持
```

**ArkTS1.2**

```typescript
let a = 1;
a = a && 2;   // 结果: 2
a = a || 3;   // 结果: 2
a = a ?? 4;   // 结果: 2
```

## 非十进制bigint字面量

**规则：**`arkts-only-support-decimal-bigint-literal`

**规则解释：**

ArkTS1.2暂不支持非十进制bigint字面量。

**变更理由：**

语言层面暂不支持。

**适配建议：**

开发者自行替换为BigInt()函数。

**示例：**

**ArkTS1.1**

```typescript
let a1: bigint = 0xBAD3n;  // 十六进制字面量，ArkTS1.2暂不支持
let a2: bigint = 0o777n;   // 八进制字面量，ArkTS1.2暂不支持
let a3: bigint = 0b101n;  // 二进制字面量，ArkTS1.2暂不支持
```

**ArkTS1.2**

```typescript
let a1: bigint = BigInt(0xBAD3);
let a2: bigint = BigInt(0o777);
let a3: bigint = BigInt(0b101);
```

## 数值类型和bigint类型的比较

**规则：**`arkts-numeric-bigint-compare`

**规则解释：**

ArkTS1.2暂不支持数值类型和bigint类型的比较。

**变更理由：**

语言层面暂不支持。

**适配建议：**

开发者需将值转换为BigInt类型再进行比较。

**示例：**

**ArkTS1.1**

```typescript
let n1: number = 123;
let n2: bigint = 456n;

n1 <= n2;   // 编译通过
n1 == n2;   // 编译失败
n1 >= n2;   // 编译通过
```

**ArkTS1.2**

```typescript
let n1: number = 123;
let n2: bigint = 456n;

BigInt(n1) <= n2;
BigInt(n1) == n2;
BigInt(n1) >= n2;
```

## 通过new创建的Number/Boolean/String对象不再是object类型

**规则：**`arkts-primitive-type-normalization`

**规则解释：**

在ArkTS1.2中，在比较Number/Boolean/String对象时会自动拆箱，比较的是它们的值而不是对象。

而在ArkTS1.1中，比较的是对象而不是值。

**变更原因：**

在ArkTS1.2中，在语言层面上基本类型和其对应的包装类型是相同的类型，这提高了语言的一致性和性能。

**适配建议：**

注意用new创建的Number/Boolean/String对象在操作时可能会有和ArkTS1.1不同的行为。

**示例：**

**ArkTS1.1**

```typescript
typeof new Number(1) // 结果："object"
new Number(1) == new Number(1);  // 结果：false
//这里if语句判断的是Boolean对象是否为空，而不是拆箱后的结果，所以结果为true
if (new Boolean(false)) {}  // 结果：true
```

**ArkTS1.2**

```typescript
typeof new Number(1)// 结果："number"
new Number(1) == new Number(1);  // 结果：true
if (new Boolean(false)) {}      // 结果：false
```

## enum的元素不能作为类型

**规则：**`arkts-no-enum-prop-as-type`

**规则解释：**

ArkTS1.2中enum（枚举）的元素不能作为类型使用。

**变更原因：**

ArkTS1.1中的枚举是编译时概念，在运行时仍是普通对象。

ArkTS1.2中枚举的每个元素是枚举类的实例，无法作为类型使用。

**适配建议：**

使用枚举类型/字符串字面量类型。

**示例：**

**ArkTS1.1**

```typescript
enum A { E = 'A' }
function foo(a: A.E) {}
```

**ArkTS1.2**

```typescript
enum A { E = 'A' }
function foo1(a: 'A') { }
function foo2(a: A) { }
```

## 不支持debugger 

**规则：**`arkts-no-debugger`

**规则解释：**

不支持debugger语句。

**变更理由：**

1. 静态类型语言具备编译时检查和强类型约束，调试通常由DevEco Studio完成，因此已具备强大的调试机制。

2. 使用debugger会侵入式地修改源码。

3. debugger语句会被优化，可能导致行为不一致。

**适配建议：**

使用DevEco Studio断点调试代替debugger语句。

**示例：**

**ArkTS1.1**

```typescript
// ArkTS1.1 
// ...
debugger;
// ...
```

**ArkTS1.2**

```typescript
// ArkTS1.2   移除debugger语句
// ...
```

## 不支持空数组/稀疏数组 

**规则：**`arkts-no-sparse-array`

**规则解释：**

ArkTS1.2要求数组元素类型明确（需上下文推导），禁止稀疏存储（避免内存浪费），且不允许undefined空位（确保空值安全）。

**变更理由：**

1. ArkTS1.2遵循静态类型。如果空数组无法根据上下文推导出元素类型，会导致编译错误。

2. ArkTS1.2的数组是连续存储的。使用空位（如 [1, , , 2]）会浪费内存。

3. ArkTS1.2遵循空值安全，无法使用默认undefined表示空缺。

**适配建议：**

为数组标注合适的类型，不使用具有空洞的数组。

**示例：**

**ArkTS1.1**

```typescript
let a = []; // ArkTS1.2，编译错误，需要从上下文中推导数组类型
let b = [1, , , 2]; // 不支持数组中的空位
b[1];  // undefined 
```

**ArkTS1.2**

```typescript
let a: number[] = [];  // 支持，ArkTS1.2上可以从上下文推导出类型
let b = [1, undefined, undefined, 2];
```

## 智能类型差异

**规则：**`arkts-no-ts-like-smart-type`

**规则解释：**

在ArkTS1.2中，线程共享对象在做[智能转换](#智能转换)时会表现的与ArkTS1.1不一致。

**变更理由：**

在ArkTS1.2中，由于线程共享对象在多线程中使用，编译器在做类型推导和分析时需要考虑并发场景下变量类型/值的变化。

**适配建议：**

线程共享对象要通过局部变量进行[智能转换](#智能转换)。

**示例：**

**ArkTS1.1**

```typescript
class AA {
  public static instance?: number;
  getInstance(): number {
    if (!AA.instance) {
      return 0;
    }
    return AA.instance;
  }
}
```

**ArkTS1.2**

```typescript
class AA {
  public static instance?: number;
  getInstance(): number {
    let a = AA.instance     // 需通过局部变量进行类型转换。
    if (!a) {
      return 0;
    }
    return a;
  }
}
```

## 数组/元组类型在继承关系中遵循不变性原则

**规则：**`arkts-array-type-immutable`

**规则解释：**

在ArkTS1.2中，数组在继承关系中遵循不变性原则，会通过编译时检查保证类型安全。

**变更理由：**

在ArkTS1.2中，数组在继承关系中遵循不变性原则，编译时检查确保类型安全，将潜在的运行时错误提前到编译期，避免运行时失败，提高执行性能。

**适配建议：**

避免将不同类型的数组互相赋值。

**示例：**

**ArkTS1.1**

```typescript
class A {
  a: number = 0;
}

class B {
  b: number = 0;
}

// ArkTS1.1 
let arr1: A[] = [new A()];
let arr2: (A | B)[] = arr1;   // ArkTS1.2编译错误
```

**ArkTS1.2**

```typescript
class A {
  a: number = 0;
}

class B {
  b: number = 0;
}

// ArkTS1.2 
let arr1: [ A | B ] = [new A()];
let arr2: [ A | B ] = arr1;  // 需要相同类型的元组
```

## 默认参数必须放在必选参数之后

**规则：**`arkts-default-args-behind-required-args`

**规则解释：**

在ArkTS1.2中，函数、方法及lamada表达式的默认参数必须放在必选参数之后。

**变更理由：**

将默认参数置于必选参数前没有实际意义，开发者仍需为每个默认参数提供值。

**适配建议：**

默认参数放在必选参数之后。

**示例：**

**ArkTS1.1**

```typescript
function add(left: number = 0, right: number) { 
  return left + right;
}
```

**ArkTS1.2**

```typescript
function add(left: number, right: number) {
  return left + right;
}
```

## class的懒加载

**规则：**`arkts-class-lazy-import`

**规则解释：**

ArkTS1.2的类默认是懒加载的。

**变更理由：**

ArkTS1.2的类默认是懒加载的，这可以提升启动性能并减少内存占用。

**适配建议：**

将类中未执行的初始化逻辑移到外部。

**示例：**

**ArkTS1.1**

```typescript
class C {
  static {
    console.info('init');  // ArkTS1.2上不会立即执行
  }
}
```

**ArkTS1.2**

```typescript
// ArkTS1.2  如果依赖没有被使用的class执行逻辑，那么将该段逻辑移出class
class C {
  static {}
}
console.info('init');
```

## 继承/实现方法时参数遵循逆变原则，返回类型遵循协变原则

**规则：**`arkts-method-inherit-rule`

**规则解释：**

ArkTS1.2继承或实现方法时，参数类型须遵循[逆变](#逆变协变)原则，返回类型遵循[协变](#逆变协变)原则。

ArkTS1.1则没有这样的限制，参数和返回类型可以逆变或协变。

**变更理由：**

参数类型逆变，可以通过编译时检查保证类型安全，提前发现潜在错误，避免运行时失败，提升执行性能。

返回类型协变，可以确保调用方按父类声明操作返回值时，所有父类声明的属性和方法必然存在。这样可以避免运行时出现属性或方法缺失的情况。

**适配建议：**

根据参数类型[逆变](#逆变协变)和返回类型[协变](#逆变协变)的原则修改实现类中的方法。

**示例：**

**ArkTS1.1**

```typescript
class A { u = 0 }
class B { v = 0 }
class Father {
  testParam(a: A) { }
  testReturn(): A | B { return new A() }
}
class Son extends Father {
  // 参数可以协变
  override testParam(a: A | B) { }
  // 返回值可以逆变
  override testReturn(): B { return new B() }
}
```

**ArkTS1.2**

```typescript
class A { u = 0 }
class B { v = 0 }
class Father {
    testParam(a: A) { }
    testReturn(): A | B { return new A() }
}
class Son extends Father {
    // 参数遵循逆变
    override testParam(a: A | B) { }
    // 返回值遵循协变
    override testReturn(): A { return new A(); }
}
```

## Enum不可以通过索引访问成员

**规则：**`arkts-enum-no-props-by-index`

**规则解释：**

ArkTS1.2强化枚举静态类型约束（运行时保留类型信息），禁止通过索引访问以替代ArkTS1.1的动态对象行为。

**变更理由：**

1. ArkTS1.1已对索引访问元素的语法做了限制，ArkTS1.2进一步增强了对枚举场景的约束。具体内容请参考[不支持通过索引访问字段](typescript-to-arkts-migration-guide.md#不支持通过索引访问字段)。

2. 在ArkTS1.1上，枚举是动态对象；而在ArkTS1.2上，枚举是静态类型，并具有运行时类型，因此对[]访问做了限制以提高性能。

**适配建议：**

通过枚举的API来实现对应功能。

**示例：**

**ArkTS1.1**

```typescript
enum TEST {
  A,
  B,
  C
}

TEST['A'];       // ArkTS1.2上不支持这种语法
TEST[0];    // ArkTS1.2上不支持这种语法
```

**ArkTS1.2**

```typescript
enum TEST {
  A,
  B,
  C
}

TEST.A;          // 使用点操作符或者enum的值
TEST.A.getName();  // 使用enum对应的方法获取enum的key
```

## 对象没有constructor

**规则：**`arkts-obj-no-constructor`

ArkTS1.2支持天然共享的能力，运行时需要确定类型信息。实现上不再基于原型的语言，而是基于class的语言。

**ArkTS1.1**

```typescript
class A {}
let a = new A().constructor;   // ArkTS1.2上编译错误
```

**ArkTS1.2**

```typescript
class A {}
let a = new A();
let cls = Type.of(a); 
```

## 子类有参构造函数需要显式定义，且必须调用父类的构造函数

**规则：**`arkts-subclass-must-call-super-constructor-with-args`

1. ArkTS1.1在运行时没有对函数调用的检查，同时利用arguments机制获取所有参数（ArkTS1.2上不支持这个特性）并传入父类构造函数。ArkTS1.2对函数参数的个数和类型会进行编译时检查，确保程序的安全和正确性，因此ArkTS1.2上不支持这种写法。

2. ArkTS1.2支持方法重载，构造函数可能有多个实现体，在ArkTS1.2上支持这个特性会造成子类继承父类时的二义性。

**ArkTS1.1**

```typescript
class A {
  constructor(a: number) {}
}
class B extends A {}                // ArkTS1.2上编译报错
let b = new B(123);
```

**ArkTS1.2**

```typescript
class A {
  constructor(a: number) {}
}
class B extends A {
  constructor(a: number) {
    super(a)
  }
}
let b = new B(123);
```

## 不支持可选元组类型

**规则：**`arkts-no-optional-tuple`

ArkTS1.2不支持可选元组类型。通过编译时检查保证类型安全，将潜在的运行时错误提前到编译期，避免运行时失败，从而提高执行性能。

**ArkTS1.1**

```typescript
let t: [number] = [1];
let t1: [number, boolean?] = t;   // ArkTS1.2编译错误
```

**ArkTS1.2**

```typescript
let t: [number] = [1];
let t1: [number, boolean] | [number] = t;
```

## 不支持超大数字字面量

**规则：**`arkts-no-big-numeric-literal`

1. ArkTS1.2支持更多数值类型细化，可以获得更好的性能。超出int/long/double范围的数字字面量会有编译错误。

2. 支持隐式转换会造成额外的性能损耗。

3. 浮点数据的隐式转换可能带来精度的损失，违反开发者预期。清晰的数值边界可以提升代码准确性和可读性。

**ArkTS1.1**

```typescript
let s = 1000000000000000000000000000000000000; // ArkTS1.1会转换成浮点形式数据，ArkTS1.2编译错误
let t = 1E+309;                               // ArkTS1.1会转换为Infinity，ArkTS1.2编译错误
```

**ArkTS1.2**

```typescript
let s = 1000000000000000000000000000000000000.0; // ok，浮点形式数据
let t = Infinity;                                // ok，值为Infinity
```

## class/interface的变量名称需要是合法标识符

**规则：**`arkts-identifier-as-prop-names`

1. ArkTS1.1上已经进行约束，ArkTS1.2对边界场景增强约束。详细内容请参考[对象的属性名必须是合法的标识符](typescript-to-arkts-migration-guide.md#对象的属性名必须是合法的标识符)。

2. 静态类型中对属性的访问是静态的，可以获得更好的执行性能。

3. 使用字符串作为属性名称可能带来二义性。

**ArkTS1.1**

```typescript
class A {
  's' = 1;
}
```

**ArkTS1.2**

```typescript
class A {
  s = 1;
}
```

## 子类不可以声明和父类的方法同名的lamada类型的属性

**规则：**`arkts-no-subclass-lamada-prop-name-same-as-superclass-method`

不同于ArkTS1.1上的动态对象（属性和方法一致），ArkTS1.2上的属性与方法有本质区别。属性用以保存类实例的状态，是可变的。方法定义类对象的行为或功能，被类的所有实例所共有，不能被改变。

同时，ArkTS1.1和ArkTS1.2不支持属性和实例方法同名。因此在ArkTS1.2上，类的继承关系中不能将同名属性和方法相互覆写。

**ArkTS1.1**

```typescript
class A {
  foo() {
    console.info('A');
  }
}

class B extends A {
  foo: () => void = () => {
    console.info('B');
  }
}
```

**ArkTS1.2**

```typescript
class A {
  foo() {
    console.info('A');
  }
}

class B extends A {
  foo() {
    console.info('B');
  }
}
```

## 子类不能在static context中调用super

**规则：**`arkts-no-super-call-in-static-context`

1. ArkTS1.2不再基于原型实现继承。没有原型/构造函数的概念，无法实现动态替换原型，因此无需通过super动态访问父类。

2. super定义在子类的静态上下文中，容易混淆super的指向，与在实例方法中super指向父类实例相冲突，造成开发者的混用。使用类名的方式访问静态成员更清晰、可维护，易于开发者理解。

**ArkTS1.1**

```typescript
class A {
  static foo() {
    return 123;
  }
}

class B extends A {
  static foo() {
    return super.foo() + 456;
  }
}
```

**ArkTS1.2**

```typescript
class A {
  static foo() {
    return 123;
  }
}

class B extends A {
  static foo() {
    return A.foo() + 456;
  }
}
```

## 类继承含属性的接口时，需要实现属性的get/set方法

**规则：**`arkts-class-implement-interface-prop-getter-setter`

ArkTS1.2遵循严格的类型检查，可以通过编译时检查保证类型安全，将潜在的运行时错误提前到编译期，避免运行时失败，从而提高执行性能。

**ArkTS1.1**

```typescript
interface I {
  v: number
}

class A implements I {
  get v(): number {
    return 1;
  }
}
```

**ArkTS1.2**

```typescript
interface I {
  readonly v: number
}

class A implements I {
  get v(): number {
    return 1;
  }
}
```

## 不能将超出枚举范围的值赋值给枚举类型的变量

**规则：**`arkts-out-of-enum-index`

ArkTS1.2上枚举类型是类型安全的，编译器会进行严格检查，避免应用中的非预期行为或错误。同时，枚举的值是编译时确定的，如果在运行时赋值超出范围的值，会对开发者造成困惑，降低易用性（TS在新版本上也增强了枚举场景的编译检查）。

**ArkTS1.1**

```typescript
enum T {
  A = 0,
  B = 1,
  C = 2
}

let num: number = 123;

let t1: T = 0;
let t2: T = -1;
let t3: T = num;
```

**ArkTS1.2**

运行时赋值枚举类型在ArkTS1.2上没有直接的替代写法。如果想超出枚举范围赋值，建议使用类/容器等其他数据结构实现。

## 不支持不定长的元组类型

**规则：**`arkts-no-unfixed-len-tuple`

ArkTS1.2上不支持可变元组，可以通过编译时检查保证类型安全，将潜在的运行时错误提前到编译期，避免运行时失败，从而提高执行性能。

**ArkTS1.1**

```typescript
const s: [string, ...boolean[]]=['', true];
```

**ArkTS1.2**

```typescript
const s: (string | boolean)[] =['', true];
```

## 类实例不支持关系表达式

**规则：**`arkts-no-class-instance-relational-expression`

1. ArkTS1.2中遵循类型安全，为避免隐式转化行为，关系表达式的操作符必须是数值类型、字符串类型、布尔类型、枚举类型。同时，支持隐式转化可能引发非预期的异常。

2. 对象的比较缺乏默认语义，为了语言的一致性和明确性，不支持不同对象的比较。

**ArkTS1.1**

```typescript
class A {
  valueOf () {
    return 3;
  }
}

class B {
  valueOf () {
    return 4;
  }
}

let a = new A();
let b = new B();
console.info('a<b:', a < b);
```

**ArkTS1.2**

```typescript
class A {
  valueOf () {
    return 3;
  }
}

class B {
  valueOf () {
    return 4;
  }
}

let a = new A();
let b = new B();
console.info(a.valueOf() < b.valueOf());
```

## instanceof的目标类型不能是函数

**规则：**`arkts-no-instanceof-func`

ArkTS1.2上不再基于原型实现继承，没有原型/构造函数的概念，不能通过任意函数创建对象。因此instanceof的目标类型不能是函数。

**ArkTS1.1**

```typescript
function foo() {}
function bar(obj: Object) {
  console.info('obj instanceof foo :' ,obj instanceof foo);
}
```

**ArkTS1.2**
```typescript
function bar(obj: Object) {
console.info('obj instanceof foo :', obj instanceof string);
}
```

## 静态加载包内模块某一文件时ohmurl路径变更

**规则：**`arkts-ohmurl-path-change`

ArkTS1.2中在静态加载包内模块某一文件时ohmurl路径必须写全，不可省略路径中的"src/main"。

**ArkTS1.1**

```typescript
// library/ets/components/Index.ets
import { MainPage } from 'library/ets/components/MainPage'
```

**ArkTS1.2**

```typescript
// library/ets/components/Index.ets
import { MainPage } from 'library/src/main/ets/components/MainPage'
```

## 逆变/协变
用来描述类型转换后的继承关系，如果A、B表示类型，f()表示类型转换，≤表示继承关系（A≤B表示A是由B派生出来的子类），则有：

- f()为逆变时，当A≤B时，有f(B)≤f(A)成立。

- f()为协变时，当A≤B时，有f(A)≤f(B)成立。

“逆”为相反的意思，即转换关系与继承关系相反，以方法参数为例说明，当类Son继承Father时，Son的方法`func1`的参数类型反而比Father更**宽泛**

“协”为一致的意思，即转换关系与继承关系相同，如下Son中的方法`func2`的参数类型比Father更**具体**

```typescript
class A { }
class B { }
class Father {
    func1(a: A) { }
    func2(a: A | B) { }
}
class Son extends Father {
    override func1(a: A | B) { }
    override func2(a: A) { }
}
```


## 智能转换
编译器在特定场景（例如instanceof检查、null检查、上下文类型推导）下能自动识别对象的具体类型，实现变量的自动转换，无需手动操作。
