# 📊 Pipeline de Dados B3 - Tech Challenge 2

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Lambda%20%7C%20Glue%20%7C%20Athena-orange.svg)](https://aws.amazon.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Sobre o Projeto

Pipeline completo de dados para **extração, processamento e análise** de dados do Ibovespa da B3, implementado como parte do Tech Challenge 2 da **FIAP - Pós Graduação em Engenharia de Dados**.

O projeto implementa uma **arquitetura serverless moderna** na AWS, seguindo as melhores práticas de engenharia de dados com foco em escalabilidade, confiabilidade e custo-efetividade.

## 🏗️ Arquitetura

![Arquitetura do Pipeline](docs/architecture.png)

### 📋 Fluxo de Dados
```
Site B3 → Python Scraper → S3 Raw → Lambda Trigger → 
Glue ETL → S3 Refined → Athena → Analytics Dashboard
```

**Documentação completa:** [📖 ARCHITECTURE.md](docs/ARCHITECTURE.md)

## ✅ Requisitos Atendidos

### 🎯 **Obrigatórios (Tech Challenge)**
- ✅ **Requisito 1:** Scraping de dados do site da B3
- ✅ **Requisito 2:** Dados brutos no S3 em formato Parquet com partição diária
- ✅ **Requisito 3:** Bucket aciona Lambda que chama job ETL no Glue
- ✅ **Requisito 4:** Lambda em Python inicia job Glue
- ✅ **Requisito 5:** Job Glue visual com transformações obrigatórias
- ✅ **Requisito 6:** Dados refinados particionados por data e ticker
- ✅ **Requisito 7:** Catalogação automática no Glue Catalog
- ✅ **Requisito 8:** Dados disponíveis e legíveis no Athena
- ✅ **Requisito 9:** Notebook Athena com visualizações gráficas

### 🚀 **Funcionalidades Extras**
- 📊 **Interface Web Completa** com Flask
- 📈 **Dashboard de Monitoramento** em tempo real
- 🔬 **Analytics Interativo** (réplica do notebook Athena)
- ☁️ **Navegador S3** integrado
- 🔍 **Interface Athena** para queries SQL
- 🎨 **Design System** consistente

## 🛠️ Tecnologias Utilizadas

### **Backend & Data Pipeline**
- **Python 3.13** - Linguagem principal
- **Flask** - Framework web
- **Playwright** - Automação de browser para scraping
- **BeautifulSoup** - Parse HTML
- **Pandas** - Manipulação e processamento de dados
- **PyArrow** - Conversão para formato Parquet

### **AWS Cloud Services**
- **Amazon S3** - Data Lake (raw + refined)
- **AWS Lambda** - Triggers serverless
- **AWS Glue** - ETL jobs + Data Catalog
- **Amazon Athena** - Query engine SQL serverless

### **Frontend & Interface**
- **HTML5/CSS3** - Interface responsiva
- **JavaScript (Vanilla)** - Interatividade
- **Matplotlib/Seaborn** - Geração de gráficos
- **Bootstrap-like Grid** - Layout responsivo

## 🚀 Instalação e Configuração

### **Pré-requisitos**
- Python 3.13+
- Conta AWS com Free Tier
- Git
- VS Code (recomendado)

### **1. Clonar o Repositório**
```bash
git clone https://github.com/seu-usuario/tech-challenge-b3.git
cd tech-challenge-b3
```

### **2. Configurar Ambiente Virtual**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### **3. Instalar Dependências**
```bash
pip install -r requirements.txt
```

### **4. Configurar Variáveis de Ambiente**
Crie um arquivo `.env` na raiz do projeto:
```env
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=us-east-2
SCRAPING_TARGET_S3_BUCKET=seu-bucket-nome
ATHENA_DATABASE=techchallenge_db
ATHENA_OUTPUT_LOCATION=s3://athena-results-bucket/
FLASK_ENV=development
```

### **5. Configurar AWS Services**

#### **S3 Bucket**
```bash
aws s3 mb s3://seu-bucket-raw --region us-east-2
```

#### **Glue Database**
```bash
aws glue create-database --database-input Name=techchallenge_db
```

#### **Lambda Function**
- Deploy via console AWS
- Código em: `src/lambda/glue_trigger.py`
- Trigger: S3 Object Created

## 🏃‍♂️ Como Executar

### **1. Iniciar Aplicação**
```bash
python app.py
```

### **2. Acessar Interface**
```
http://localhost:5000
```

### **3. Executar Pipeline**
1. Acesse a **página inicial**
2. Clique em **"Executar Raspagem"**
3. Aguarde processamento (~5 minutos)
4. Verifique dados no **Dashboard**

### **4. Análises Avançadas**
- **Analytics:** `/analytics` - Análises visuais interativas
- **Dashboard:** `/dashboard` - Monitoramento do sistema
- **S3 Navigator:** `/s3_navigator` - Explorar dados
- **Athena Queries:** `/athena_query` - SQL interativo

## 📊 Estrutura do Projeto

```
tech_challenger_2/
├── 📁 src/                          # Código fonte principal
│   ├── 📁 routes/                   # Rotas Flask (web + API)
│   ├── 📁 services/                 # Lógica de negócio
│   ├── 📄 b3_extractor.py          # Scraper principal
│   ├── 📄 orchestrator.py          # Orquestração do pipeline
│   └── 📄 config.py                # Configurações
├── 📁 templates/                    # Templates HTML
│   ├── 📄 index.html               # Página inicial
│   ├── 📄 dashboard.html           # Dashboard de monitoramento
│   ├── 📄 analytics.html           # Analytics interativo
│   └── 📄 base.html                # Template base
├── 📁 static/                       # Assets estáticos
│   ├── 📁 css/                     # Estilos
│   └── 📁 js/                      # JavaScript
├── 📁 docs/                         # Documentação
│   ├── 📄 ARCHITECTURE.md          # Arquitetura detalhada
│   └── 🖼️ architecture.png         # Diagrama visual
├── 📄 app.py                       # Aplicação Flask principal
├── 📄 requirements.txt             # Dependências Python
├── 📄 Procfile                     # Deploy (Heroku/Railway)
├── 📄 .env.example                 # Exemplo de variáveis
└── 📄 README.md                    # Este arquivo
```

## 📈 Funcionalidades Principais

### **🔄 Pipeline Automatizado**
- **Scraping automático** do site B3
- **Processamento ETL** via AWS Glue
- **Particionamento inteligente** por data/ticker
- **Catalogação automática** de metadados

### **📊 Interface Web Completa**
- **Dashboard executivo** com métricas em tempo real
- **Analytics interativo** com gráficos e insights
- **Navegador S3** para exploração de dados
- **Console Athena** para queries SQL customizadas

### **🔍 Análises Disponíveis**
- **Composição do Ibovespa** por participação
- **Análise por tipo de ação** (ON, PN, UNT)
- **Concentração do índice** (curva de Lorenz)
- **Ranking das principais ações**
- **Métricas estatísticas** descritivas

## 🎯 Resultados e Insights

### **📊 Dados Processados**
- **~15 ações** do Ibovespa por execução
- **Formato Parquet** (50% menor que CSV)
- **Particionamento otimizado** para queries
- **Schema evolution** suportado

### **⚡ Performance**
- **Scraping:** ~30 segundos
- **ETL Glue:** ~3-5 minutos  
- **Query Athena:** <10 segundos
- **Interface web:** <2 segundos

### **💰 Custo Otimizado**
- **Free Tier friendly:** ~$5-10/mês
- **Serverless:** Pay-per-use
- **S3 Intelligent Tiering:** Economia automática

## 🧪 Testes e Validação

### **Testes Implementados**
- ✅ Conectividade AWS
- ✅ Validação de dados scraped
- ✅ Schema Parquet
- ✅ Particionamento S3
- ✅ Queries Athena

### **Monitoramento**
- 📊 Dashboard de métricas
- 🔍 Logs estruturados
- ⚠️ Alertas de erro
- 📈 Tracking de performance

## 🔒 Segurança e Boas Práticas

- **IAM Roles** com permissões mínimas
- **Credenciais** via variáveis de ambiente
- **Encryption at rest** (S3)
- **Code review** e versionamento Git
- **Error handling** robusto

## 📚 Documentação Adicional

- **[Arquitetura Completa](docs/ARCHITECTURE.md)** - Diagramas e fluxos detalhados
- **[Configuração AWS](docs/AWS_SETUP.md)** - Guia de setup dos serviços
- **[API Reference](docs/API.md)** - Documentação das APIs
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Resolução de problemas

## 🤝 Contribuição

Este projeto foi desenvolvido como parte do **Tech Challenge 2** da FIAP. Contribuições e sugestões são bem-vindas!

### **Como Contribuir**
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💼 Autor

**Willian do Prado Vieira**
- 🎓 **FIAP** - Pós Graduação em Engenharia de Dados
- 💼 **LinkedIn:** [willian-do-prado-vieira](https://br.linkedin.com/in/willian-do-prado-vieira-87348659)
- 📧 **Email:** willian@email.com
- 🐙 **GitHub:** [@willianprado](https://github.com/willianprado)

## 🏆 Reconhecimentos

- **FIAP** pela excelente estrutura do Tech Challenge
- **AWS** pelos serviços cloud robustos e Free Tier
- **B3** pelos dados públicos disponibilizados
- **Comunidade Python** pelas ferramentas open source

---

## 🚀 Deploy e Demonstração

### **📹 Vídeo Demonstrativo**
[🎬 Link para o vídeo de demonstração](https://youtu.be/seu-video)

### **🌐 Demo Online**
[🔗 Aplicação em produção](https://seu-deploy.herokuapp.com)

### **📊 Athena Notebook**
[📓 Análises no AWS Console](https://console.aws.amazon.com/athena/notebooks)

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**

**📞 Dúvidas? Abra uma issue ou entre em contato!**