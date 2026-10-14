# 怎么把项目上传到 GitHub

> 仓库文件已经在本机准备好了，路径是 `杂项/点点农场-复刻版/`。
> 下面三种方式**任选一种**。推荐第 1 种（GitHub Desktop），全程鼠标操作。

---

## ⚠️ 先注意一件事：文件数量

仓库里有 **339 张素材图片 + 十来个文档**。

- GitHub 网页版的「拖拽上传」**一次最多 100 个文件**，素材太多会失败
- 所以**不要**用网页拖拽上传，用下面第 1 或第 2 种方式

---

## 方式 1：GitHub Desktop（推荐，全鼠标操作）

1. 下载安装：https://desktop.github.com/ ，用你的 GitHub 账号登录
2. 打开软件 → 菜单 `File` → `Add Local Repository...`
3. 文件夹选：`C:\Users\15716\Desktop\31577\杂项\点点农场-复刻版`
   - 如果它提示"这个目录还不是 git 仓库"，点 **Create a repository**（创建仓库），
     名字填 `diandian-farm`，**其他选项都别勾**，直接 Create
4. 左下角 Summary 填 `first commit` → 点 **Commit to main**
5. 右上角点 **Publish repository**
   - 名字 `diandian-farm`，描述随便写
   - **勾掉 / 不要勾** "Keep this code private"（除非你想设为私有）
   - 点 Publish
6. 等它传完（几分钟），打开 github.com 就能看到了

---

## 方式 2：命令行（如果你装了 Git）

在 `杂项/点点农场-复刻版/` 目录里依次执行：

```bash
git init
git add .
git commit -m "first commit: 点点农场复刻版"
git branch -M main
git remote add origin https://github.com/你的用户名/diandian-farm.git
git push -u origin main
```

（先在 github.com 网页上建一个空仓库，名字叫 `diandian-farm`，不要勾 README）

---

## 方式 3：网页上传（不推荐，但想试的话）

因为超过 100 个文件，需要**分批**上传：先传文档和 `src/`、`data/`，
再分 4 批传 `assets/` 的各个子文件夹。麻烦且容易漏，**不建议**。

---

## 传完之后建议做的几件小事

1. **仓库描述**（About）写一句：
   `快易典「点点农场」网页复刻版 · 数据全部来自 T5 固件逆向提取 · 单文件 HTML 双击即玩`
2. **Topics** 加几个标签：`farm-game` `retro` `reverse-engineering` `html5` `single-file`
3. 勾选 README 里提到的版权声明——素材来自原厂固件，非商业用途，这点很重要
4. 如果想让别人更容易找到游戏入口，可以在仓库设置里**开 GitHub Pages**：
   `Settings → Pages → Source 选 main / root`，
   之后会得到一个网址，别人打开就能直接玩（不用下载）

---

## 如果要更新

改了文件之后（GitHub Desktop）：

1. 软件会自动发现改动
2. 左下角写 Summary → Commit
3. 右上角 **Push origin**

就同步上去了。
