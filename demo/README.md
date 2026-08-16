# Domain-First Function Contract Demo

本 Demo 不是万能解析器。它只验证两件事：

1. 受限 EML AST 能否在固定分支策略下返回可复查的值、失效状态和反例；
2. 有限自映射是否先满足域闭合，再逐点满足 `g(g(x)) = f(x)`。

## 运行

```powershell
python demo/run_demo.py
python -m pytest -q demo/test_demo.py
```

依赖：Python 3.14、SymPy 1.14。代码不使用 `eval`、`exec` 或裸 `sympify`。

## 产物

- `artifacts/demo/results.json`
- `artifacts/demo/events.jsonl`
- `artifacts/demo/EVAL.md`
- `artifacts/demo/lean_status.txt`

## 解释边界

- `compiled_ln` 是 E1 中 `ln(x)` 的 EML 编译树。
- 负实轴上的主分支符号差异是 E1 已知问题，本 Demo 只是复现，不是新发现。
- 数值一致只记作测试通过，不写成形式证明。
- 固定 Lean `v4.29.0-rc6` 已实际运行：`demo/lean/FunctionContract.lean` 编译通过；上游 `prime_loop_verification/eml_verification/eml.lean` 被接受但 `reconstruct_ln` 含 `sorry`，故总体只算部分形式化。
