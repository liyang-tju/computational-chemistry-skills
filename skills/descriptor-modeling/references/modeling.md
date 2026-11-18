# 建模与验证

## 1. 防泄漏 Pipeline 与分组验证模板

严禁在划分数据集之前就做全表 `StandardScaler` 或基于全局相关性筛选 Top-K 特征。统一使用 `sklearn.pipeline.Pipeline` 配合分组切分器：

```python
import numpy as np
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV

pipe = make_pipeline(
    StandardScaler(),
    RidgeCV(alphas=np.logspace(-3, 3, 25))
)

gkf = GroupKFold(n_splits=min(5, len(set(groups))))
y_cv = cross_val_predict(pipe, X, y, groups=groups, cv=gkf)

rmse_cv = float(np.sqrt(np.mean((y - y_cv) ** 2)))
mae_cv = float(np.mean(np.abs(y - y_cv)))
r2_cv = float(1.0 - np.sum((y - y_cv) ** 2) / np.sum((y - np.mean(y)) ** 2))
print(f"GroupKFold -> R2={r2_cv:.3f}, RMSE={rmse_cv:.3f}, MAE={mae_cv:.3f}")
```

- **关于选公式偏差（Selection Bias）**：如果用 SISSO 从数万个特征组合中挑出 1 条表达式，再用同一个全数据集做 5 折交叉验证来评估这条固定公式，得到的 CV 误差依然偏乐观；正确做法是在每个外层训练折内独立运行 SISSO 搜索并在对应的外层验证折上评估（Nested CV），或保留完全未参与搜索的独立测试组。

## 2. 样本粒度与“生态谬误”辨析

在不同数据聚合层级拟合的模型，物理意义截然不同，不可混为一谈：
- **物种/条件均值模型**：例如对 8 个不同吸附物在不同电势下的时间均值 $\bar{y}$ 拟合；解释的是“跨体系平均差异”，但**无法解释同一条轨迹内部随时间涨落的原因**。
- **单帧瞬时模型**：通常受大量构型/热涨落噪音影响，且同轨迹相邻帧高度自相关；可做**组内中心化（within-group centering）**诊断，检验同一体系内的涨落是否也遵循相同规律，但组内模型不可直接等同于跨体系模型。

## 3. 共线性、小样本与表达式检查

- 小数据集（例如 $N < 20$）下引入多变量组合极易发生共线性过拟合：哪怕训练 $R^2 > 0.95$，系数的正负号和大小也可能随删掉 1 个样本就剧烈翻转（高 VIF），此时切忌基于回归系数正负号硬讲物理机理。
- **SISSO / 符号表达式交付要求**：
  1. 写出包含常数项与全部符号算子的完整可读表达式；
  2. 核查每一步加减运算两侧是否保持一致的物理量纲，或明确说明无量纲归一化基准；
  3. 明确指出超出训练域范围（例如更高电势、不同晶面或不同溶剂）时的外推风险。
