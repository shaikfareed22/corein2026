# corein 品牌

2026-10-20 定稿。标志、字标和应用图标是同一个决定；应用内的配色沿用分叉前的体系，因为标志本身就是墨色加蓝色，与应用已经一致。

## 标志

**电路 o**：一个圆环，环内三条走线，各自以一个节点收尾。它是字标里的 o，单独使用时就是应用图标。画成 100 单位画布上的一条复合填充路径，所有生成脚本原样读取。

- 源文件：`assets/brand/corein-mark.svg`，其余全部由它派生。
- `assets/brand/corein-icon.svg`：白色圆角方块（`rx=27`）、一圈细边、标志。凡是图标代表应用的地方（README、网站、favicon）都用它。
- `assets/brand/corein-icon-on-dark.svg`：深色方块上的白色标志，只用于商店页和启动画面。
- `assets/brand/corein-wordmark.svg`：小写 **corein**，粗几何无衬线，o 换成标志。放在浅色底上；深色底上反白。
- `assets/brand/corein-cover.svg`：README 头图。
- `docs/app-icon.png`：512 px 圆角方块，图标在主屏上的样子。

图标**不是**吉祥物。默认的脸是内置的小龙；不要把小龙放到启动图标上，也不要把电路 o 当成聊天里的脸。

## 颜色

| 名称 | 值 | 用途 |
|---|---|---|
| `brand.ink.start` | `#0B0F19` | 标志渐变左端 |
| `brand.ink.end` | `#1A2233` | 标志渐变右端 |
| `tile` | `#FFFFFF` | 图标底块 |
| `tile.dark` | `#0F1B33` | 深色底块 |
| `brand.blue` | `#015CFB` | 链接、主按钮、状态行（应用内不变） |

应用的明暗主题色不变：`primary` `#015CFB`、`primary.container` `#E5F0FF`、`ink` `#000000`、`pill` `#F2F2F7`。

## 规则

- 正文和字标里一律小写 `corein`；只有平台强制首字母大写时才例外。
- 标志不拉伸、不描边、不加投影。
- 字标四周留白为 o 的高度。
- 最小尺寸：标志 16 px，字标宽 80 px。

## 重新生成图标

```sh
python scripts/gen-android-icons.py
python scripts/gen-ios-icons.py
```

两者都读 `assets/brand/corein-mark.svg`，位图需要装有 Chromium 的 Playwright。
