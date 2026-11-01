# CoralNet + SAM: Segmentação Bêntica 100% Automatizada

Pipeline híbrido que combina a geometria do **Meta Segment Anything (SAM ViT-H)** executando na nuvem gratuita do **Google Colab (GPU Tesla T4 de 16 GB)** com a taxonomia do **CoralNet (EfficientNet-B0)** executando localmente no seu computador.

---

## 🏗️ Arquitetura do Sistema

```text
┌───────────────────────────────────────┐            ┌─────────────────────────────────────────┐
│     SEU COMPUTADOR (Local)            │            │       GOOGLE COLAB (Nuvem)              │
│     [D:\coralnet-sam]                 │            │       [GPU Tesla T4 de 16 GB]           │
├───────────────────────────────────────┤            ├─────────────────────────────────────────┤
│ 1. Imagens de campo e scripts         │            │ 1. Carrega o modelo SAM ViT-H (2.5 GB)  │
│ 2. Envia a foto via HTTP POST ────────┼───────────►│ 2. Segmenta 100% das colônias em ~1-2s  │
│ 3. Recebe os polígonos/máscaras ◄─────┼────────────┤ 3. Devolve centróides e coordenadas     │
│ 4. Classificador CoralNet local       │ (Túnel     │                                         │
│    (EfficientNet-B0) identifica       │  ngrok)    │                                         │
│    os 11 gêneros e gera o mapa final  │            │                                         │
└───────────────────────────────────────┘            └─────────────────────────────────────────┘
```

---

## 🗂️ Estrutura do Projeto

```text
D:\coralnet-sam\
├── colab/
│   └── sam_server_colab.ipynb # Notebook pronto para abrir e rodar no Google Colab
├── models/
│   └── efficientnet_b0_ver1.pth # Pesos locais do CoralNet copiados
├── images/                    # 8 fotos de transectos de recifes organizadas
├── src/
│   ├── sam_client.py          # Cliente HTTP para se comunicar com o Colab
│   ├── coral_classifier.py    # Classificador taxonômico com EfficientNet-B0 local
│   └── pipeline.py            # Fusão de máscaras + cálculo de cobertura e áreas
├── run_pipeline.py            # Executável CLI principal
├── requirements.txt           # Dependências locais
└── README.md
```

---

## 🚀 Como Executar

### Passo 1: Iniciar o SAM no Google Colab
1. Abra o [Google Colab](https://colab.research.google.com/).
2. Faça upload do notebook [colab/sam_server_colab.ipynb](file:///D:/coralnet-sam/colab/sam_server_colab.ipynb).
3. No menu, verifique se o ambiente de execução está com GPU (**Ambiente de execução > Alterar tipo de ambiente de execução > GPU T4**).
4. Execute todas as células.
5. Ao final, a última célula exibirá a URL pública gerada pelo túnel, por exemplo:
   `👉 https://xxxx-xx-xx.ngrok-free.app`

---

### Passo 2: Executar no seu computador local
Abra o PowerShell na pasta do projeto:

```powershell
cd D:\coralnet-sam

# Crie e ative o ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instale as dependências
pip install -r requirements.txt

# Execute o pipeline passando a URL gerada pelo Colab
python run_pipeline.py --image images/10.0_P5112664.JPG --sam-url https://xxxx-xx-xx.ngrok-free.app
```

*(Se você rodar sem o `--sam-url`, o script executa um teste local demonstrativo com grade representativa usando os pesos locais do CoralNet).*

---

### 📊 Resultados Gerados
O relatório com a contagem de colônias e porcentagem real de cobertura bêntica é impresso no terminal, e o **mapa de segmentação semântica colorida em alta definição** é salvo na pasta `output/`.
