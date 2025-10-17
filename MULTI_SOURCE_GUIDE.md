# 📚 多数据源文献检索指南

本指南介绍如何使用新增的多个医疗文献数据库进行检索。

---

## 🎯 支持的数据源

### 1. **PubMed** (原有)
- **数据量**: 35M+ 生物医学文献
- **覆盖**: MEDLINE, PubMed Central (PMC)
- **特点**: 最全面的生物医学数据库
- **费用**: 完全免费
- **API文档**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

### 2. **Semantic Scholar** (新增) ⭐
- **数据量**: 200M+ 学术论文
- **覆盖**: 计算机科学、医学、生物学等
- **特点**:
  - AI驱动的智能搜索
  - 引用计数和影响力分析
  - 论文推荐系统
  - 开放获取PDF链接
- **费用**: 免费（有API密钥可提高速率）
- **API文档**: https://api.semanticscholar.org/

### 3. **Europe PMC** (新增) ⭐
- **数据量**: 40M+ 生命科学文献
- **覆盖**: PubMed + PMC + 预印本(bioRxiv, medRxiv)
- **特点**:
  - 全文访问
  - 预印本支持
  - 开放获取重点
  - 欧洲医学研究
- **费用**: 完全免费
- **API文档**: https://europepmc.org/RestfulWebService

---

## 🚀 快速开始

### 使用单个数据源

```python
from src.data_sources import (
    PubMedClient,
    SemanticScholarClient,
    EuropePMCClient
)

# PubMed (原有方式)
pubmed = PubMedClient(email="your@email.com")
articles = pubmed.search_and_fetch("diabetes", max_results=10)

# Semantic Scholar (新)
semantic = SemanticScholarClient()
articles = semantic.search_and_fetch(
    "diabetes machine learning",
    max_results=10,
    fields_of_study=["Medicine", "Computer Science"]
)

# Europe PMC (新)
europe_pmc = EuropePMCClient(email="your@email.com")
articles = europe_pmc.search_and_fetch(
    "COVID-19 vaccine",
    max_results=10,
    sort="cited"  # 按引用数排序
)
```

### 使用统一搜索接口 🔥

```python
from src.data_sources import UnifiedSearchClient

# 初始化（会自动加载所有可用数据源）
client = UnifiedSearchClient(
    pubmed_email="your@email.com",
    semantic_scholar_api_key=None,  # 可选
    europe_pmc_email="your@email.com"
)

# 搜索单个数据源
articles = client.search_single_source(
    source="semantic_scholar",
    query="diabetes treatment",
    max_results=10
)

# 同时搜索所有数据源（并行）
all_results = client.search_all_sources(
    query="COVID-19 vaccine",
    max_results_per_source=5
)

# 结果格式：
# {
#     'pubmed': [article1, article2, ...],
#     'semantic_scholar': [article3, article4, ...],
#     'europe_pmc': [article5, article6, ...]
# }

# 搜索并合并结果（自动去重和排序）
merged_articles = client.search_and_merge(
    query="diabetes machine learning",
    max_results_per_source=10,
    total_max_results=20,
    deduplicate=True,
    sort_by="citation_count"  # 按引用数排序
)
```

---

## 💡 使用场景

### 场景1: 全面文献综述

需要最全面的文献覆盖时，使用统一搜索：

```python
client = UnifiedSearchClient()

# 搜索所有数据源
results = client.search_and_merge(
    "CRISPR gene editing 2024",
    max_results_per_source=20,
    total_max_results=50,
    sort_by="citation_count"
)

# 获取统计信息
stats = client.get_statistics(
    client.search_all_sources("CRISPR gene editing", 20)
)
print(f"Total articles: {stats['total_articles']}")
print(f"Open access: {stats['open_access_count']}")
```

### 场景2: 查找高影响力论文

使用Semantic Scholar的引用计数功能：

```python
semantic = SemanticScholarClient()

articles = semantic.search_and_fetch(
    "machine learning healthcare",
    max_results=20,
    fields_of_study=["Medicine", "Computer Science"]
)

# 按引用数排序
sorted_articles = sorted(
    articles,
    key=lambda x: x.get('citation_count', 0),
    reverse=True
)

for article in sorted_articles[:5]:
    print(f"{article['title']}")
    print(f"Citations: {article['citation_count']}")
    print(f"Open Access: {article['open_access']}")
    if article['pdf_url']:
        print(f"PDF: {article['pdf_url']}")
    print()
```

### 场景3: 获取开放获取PDF

查找有免费PDF的论文：

```python
# 方法1: Semantic Scholar
semantic = SemanticScholarClient()
articles = semantic.search_and_fetch(
    "diabetes treatment",
    max_results=20,
    open_access_only=True  # 只要开放获取
)

# 方法2: Europe PMC
europe_pmc = EuropePMCClient()
articles = europe_pmc.search_and_fetch("diabetes", max_results=20)

# 过滤出有PDF的
with_pdf = [a for a in articles if a.get('pdf_url')]
print(f"Found {len(with_pdf)} articles with PDF")
```

### 场景4: 追踪最新预印本

使用Europe PMC查找最新预印本（未经同行评审）：

```python
europe_pmc = EuropePMCClient()

# 搜索预印本
preprints = europe_pmc.search_preprints(
    "COVID-19 vaccine",
    max_results=10
)

for article in preprints:
    print(f"Title: {article['title']}")
    print(f"Date: {article['pub_date']}")
    print(f"Source: bioRxiv/medRxiv")
    print()
```

### 场景5: 论文推荐

基于某篇论文获取相关推荐：

```python
semantic = SemanticScholarClient()

# 先找到一篇相关论文
articles = semantic.search_and_fetch("diabetes", max_results=1)

if articles:
    paper_id = articles[0]['id']

    # 获取推荐论文
    recommendations = semantic.get_recommendations(
        paper_id,
        max_results=10
    )

    print(f"Based on: {articles[0]['title']}")
    print(f"\nRecommended papers:")
    for rec in recommendations:
        print(f"- {rec['title']}")
```

---

## ⚙️ 配置

### 环境变量

在 `.env` 文件中添加（可选）：

```bash
# Semantic Scholar API密钥（可选，提高速率限制）
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# Europe PMC配置
EUROPE_PMC_EMAIL=your@email.com

# 数据源偏好设置
DEFAULT_DATA_SOURCE=unified  # pubmed, semantic_scholar, europe_pmc, unified
```

### API密钥获取

#### Semantic Scholar
1. 访问 https://www.semanticscholar.org/product/api
2. 注册账号
3. 申请API密钥（可选，免费tier足够）
4. 添加到 `.env`: `SEMANTIC_SCHOLAR_API_KEY=your_key`

**注意**: 没有API密钥也可以使用，只是速率限制更低。

---

## 📊 数据源比较

| 特性 | PubMed | Semantic Scholar | Europe PMC |
|------|--------|------------------|------------|
| **数据量** | 35M+ | 200M+ | 40M+ |
| **覆盖领域** | 生物医学 | 全领域 | 生命科学 |
| **引用计数** | ❌ | ✅ | ✅ |
| **开放PDF** | 部分 | 多 | 多 |
| **全文访问** | 部分 | ❌ | ✅ |
| **预印本** | ❌ | ❌ | ✅ |
| **推荐系统** | ❌ | ✅ | ❌ |
| **速率限制** | 3/秒 | 10/秒 | 宽松 |
| **需要密钥** | ❌ | ❌ | ❌ |

### 何时使用哪个？

- **PubMed**: 标准生物医学文献搜索
- **Semantic Scholar**: 需要引用分析、跨学科研究、AI推荐
- **Europe PMC**: 需要全文、预印本、欧洲研究
- **Unified Search**: 需要全面覆盖，不确定用哪个

---

## 🔧 高级用法

### 自定义搜索参数

#### Semantic Scholar

```python
articles = semantic.search_and_fetch(
    query="cancer immunotherapy",
    max_results=20,
    year="2020-2024",  # 时间范围
    fields_of_study=["Medicine", "Biology"],
    open_access_only=True
)
```

#### Europe PMC

```python
articles = europe_pmc.search_and_fetch(
    query="diabetes treatment",
    max_results=20,
    source="MED",  # MED=PubMed, PMC=全文, PPR=预印本
    sort="cited"   # relevance, cited, date
)
```

### 并行搜索优化

```python
# 自动并行搜索所有数据源
client = UnifiedSearchClient()

results = client.search_all_sources(
    query="machine learning diagnosis",
    max_results_per_source=10,
    parallel=True  # 默认为True，速度快3倍
)
```

### 去重和合并

```python
# 自动去重（基于DOI和标题）
merged = client.search_and_merge(
    query="COVID-19",
    max_results_per_source=20,
    deduplicate=True,  # 去除重复
    sort_by="citation_count"
)

# 手动控制
results = client.search_all_sources("COVID-19", 10)
all_articles = []
for source, articles in results.items():
    all_articles.extend(articles)

# 自定义去重逻辑
seen_dois = set()
unique = []
for article in all_articles:
    doi = article.get('doi', '')
    if doi and doi not in seen_dois:
        seen_dois.add(doi)
        unique.append(article)
```

### 获取完整文本

```python
# Europe PMC支持全文
europe_pmc = EuropePMCClient()

# 搜索文章
articles = europe_pmc.search_and_fetch("diabetes", max_results=1)

if articles:
    article_id = f"PMC:{articles[0]['id']}"

    # 获取全文XML
    full_text = europe_pmc.get_full_text(article_id)

    if full_text:
        print("Full text retrieved!")
        # 处理XML内容
```

---

## 🎓 实践示例

### 示例1: 系统综述

```python
"""进行系统文献综述"""
from src.data_sources import UnifiedSearchClient

client = UnifiedSearchClient()

# 第一阶段：广泛搜索
broad_results = client.search_and_merge(
    query="artificial intelligence medical diagnosis",
    max_results_per_source=50,
    total_max_results=100,
    sort_by="citation_count"
)

print(f"Found {len(broad_results)} articles")

# 第二阶段：筛选高质量论文
high_quality = [
    a for a in broad_results
    if a.get('citation_count', 0) > 50  # 至少50次引用
]

print(f"High quality: {len(high_quality)} articles")

# 第三阶段：获取开放获取全文
open_access = [a for a in high_quality if a.get('open_access')]
print(f"Open access: {len(open_access)} articles")

# 导出结果
import json
with open('systematic_review.json', 'w') as f:
    json.dump(open_access, f, indent=2)
```

### 示例2: 文献追踪

```python
"""追踪特定主题的最新进展"""
from src.data_sources import SemanticScholarClient, EuropePMCClient
from datetime import datetime, timedelta

# 最近3个月
recent_cutoff = datetime.now() - timedelta(days=90)
year = recent_cutoff.year

# Semantic Scholar - 最新研究
semantic = SemanticScholarClient()
recent_papers = semantic.search_and_fetch(
    "CRISPR therapeutics",
    max_results=20,
    year=str(year)
)

# Europe PMC - 包括预印本
europe_pmc = EuropePMCClient()
recent_preprints = europe_pmc.search_preprints(
    "CRISPR therapeutics",
    max_results=10
)

# 合并并按日期排序
all_recent = recent_papers + recent_preprints
all_recent.sort(
    key=lambda x: x.get('pub_date', ''),
    reverse=True
)

print("最新进展：")
for article in all_recent[:10]:
    print(f"- {article['title']} ({article['pub_date']})")
```

### 示例3: 引文分析

```python
"""分析论文影响力"""
from src.data_sources import SemanticScholarClient

semantic = SemanticScholarClient()

# 搜索特定主题
articles = semantic.search_and_fetch(
    "deep learning medical imaging",
    max_results=50,
    fields_of_study=["Medicine", "Computer Science"]
)

# 分析引用分布
citation_counts = [a.get('citation_count', 0) for a in articles]

print(f"Total articles: {len(articles)}")
print(f"Average citations: {sum(citation_counts)/len(articles):.1f}")
print(f"Max citations: {max(citation_counts)}")
print(f"Highly cited (>100): {len([c for c in citation_counts if c > 100])}")

# 找出最有影响力的论文
top_papers = sorted(
    articles,
    key=lambda x: x.get('citation_count', 0),
    reverse=True
)[:10]

print("\nTop 10 most cited:")
for i, paper in enumerate(top_papers, 1):
    print(f"{i}. {paper['title']}")
    print(f"   Citations: {paper['citation_count']}")
    print(f"   Year: {paper['pub_date']}")
```

---

## 📈 性能提示

### 1. 使用缓存

```python
# 所有客户端默认启用缓存
client = UnifiedSearchClient(enable_cache=True)

# 首次搜索：2-3秒
articles1 = client.search_single_source("pubmed", "diabetes", 10)

# 第二次相同搜索：0.001秒（从缓存）
articles2 = client.search_single_source("pubmed", "diabetes", 10)
```

### 2. 并行搜索

```python
# 使用并行搜索节省时间
results = client.search_all_sources(
    "COVID-19",
    max_results_per_source=10,
    parallel=True  # 3个数据源并行，速度快3倍
)
```

### 3. 按需获取详情

```python
# 只获取ID，稍后按需获取详情
semantic = SemanticScholarClient()
paper_ids = semantic.search("diabetes", max_results=100)

# 只获取前10个的详细信息
articles = semantic.fetch_details(paper_ids[:10])
```

---

## 🐛 故障排除

### 问题1: "No module named 'src.data_sources.semantic_scholar_client'"

**解决方案**: 确保从项目根目录运行
```bash
cd /path/to/med_paper
python your_script.py
```

### 问题2: Semantic Scholar速率限制

**解决方案**: 获取API密钥或减慢请求速度
```python
semantic = SemanticScholarClient(api_key="your_key")
```

### 问题3: Europe PMC返回空结果

**解决方案**: 检查查询语法，尝试更简单的查询
```python
# ✓ 好的查询
articles = europe_pmc.search_and_fetch("diabetes", 10)

# ✗ 可能失败的查询
articles = europe_pmc.search_and_fetch("diabetes[Title/Abstract]", 10)
```

---

## 📚 参考资料

- **Semantic Scholar API**: https://api.semanticscholar.org/
- **Europe PMC API**: https://europepmc.org/RestfulWebService
- **PubMed E-utilities**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

---

## 🎯 总结

现在你有**3个强大的医学文献数据源**：

1. **PubMed**: 标准医学文献（35M+）
2. **Semantic Scholar**: AI驱动，引用分析（200M+）
3. **Europe PMC**: 全文+预印本（40M+）

使用**统一搜索接口**可以：
- ✅ 同时搜索所有数据源
- ✅ 自动去重和合并
- ✅ 按引用数排序
- ✅ 获取开放获取PDF
- ✅ 并行搜索节省时间

**立即开始使用多数据源检索，获取更全面的文献覆盖！** 🚀
