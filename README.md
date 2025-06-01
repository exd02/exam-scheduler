# Projeto Exam Scheduler

Este repositório contém três módulos principais que, em conjunto, permitem:

1. **Extrair dados de recuperação de alunos a partir de planilhas .xlsx**  
2. **Marcar exames em sala de aula (GUI interativa)**  
3. **Gerar planilhas de horário de exames otimizado via CP-SAT + exportar Excel**  

---

## 1. Visão geral dos módulos

### Módulo 1: GUI de Extração de Alunos em Recuperação  
- **Objetivo**: permitir ao usuário selecionar uma ou mais planilhas `.xlsx`, informar quais colunas devem ser consideradas (cabeçalhos) e quais linhas contêm as notas dos alunos, para então extrair e mesclar todas essas informações em um JSON único `dados/AlunosEmRecuperacao.json`.  
- **Arquivos principais**:  
  - `src/gui_recovery_extractor.py`  
    - Interface Flet que solicita o upload das planilhas, recebe cabeçalhos e linhas de início/fim, e chama a rotina de extração.  
    - Usa `recovery_utils.py` (para ler e processar cada planilha) e a função de confirmação/gravação de JSON (`json_operations.py`).  
  - `src/recovery_utils.py`  
    - Contém funções para **ler** cada arquivo XLSX (`openpyxl`), filtrar notas abaixo de 6.0, e montar um dicionário Python.  
    - Oferece `extract_json(...)` e `merge_jsons(...)` para transformar cada planilha em JSON e depois mesclar múltiplos JSONs em um único dicionário.  
  - `src/json_operations.py`  
    - Contém `confirm_and_save(...)`, que exibe um diálogo de confirmação se o arquivo de destino já existe e, em seguida, salva o JSON em disco ou sobrescreve conforme escolha do usuário, exibindo um SnackBar de sucesso.

---

### Módulo 2: GUI de Agendamento de Exames em Sala  
- **Objetivo**: permitir ao usuário visualizar, em formato de tabela, os slots de aula por curso e marcar quais disciplinas terão exame em cada slot. O resultado é gravado em `dados/ExamesEmAula.json`, que será lido posteriormente pelo pipeline de agendamento.  
- **Arquivos principais**:  
  - `src/gui_scheduler.py`  
    - Interface Flet que carrega os JSONs `dados/Horarios.json` e `dados/Dias.json`, exibe a tabela de horários para cada dia/slot e permite ao usuário clicar em células para indicar exame.  
    - Ao clicar em “Exportar configuração”, compõe o JSON de exames por curso e chama `confirm_and_save(...)` (de `json_operations.py`) para persistir em disco.  
  - `src/json_operations.py`  
    - Reutilizado aqui para exibir diálogo de confirmação caso `dados/ExamesEmAula.json` já exista, e salvar a nova configuração.

---

### Módulo 3: Pipeline CP-SAT + Excel Exporter  
- **Objetivo**: carregar todos os JSONs de dados brutos gerados (Horários, Recuperação e Exames em Sala), construir um modelo CP-SAT para alocar as provas de recuperação em slots livres, garantir restrições (máximo 3 exames por aluno por dia, sincronização entre cursos, etc.) e, em seguida, gerar planilhas `.xlsx` para cada curso com o resultado final.  
- **Arquivos principais**:  
  - `src/data_loader.py`  
    - Carrega `dados/Horarios.json`, `dados/AlunosEmRecuperacao.json`, `dados/Dias.json` e `dados/ExamesEmAula.json`.  
    - Monta estruturas auxiliares:  
      - `subjects_by_course` (disciplinas por curso),  
      - `subjects_by_student` (disciplinas por aluno),  
      - `courses_by_subject` (cursos por disciplina),  
      - `free_slots` (slots livres por curso),  
      - `daily_slot_ranges` (intervalos de slots por dia).  
  - `src/scheduler.py`  
    - Constrói o modelo CP-SAT do OR-Tools:  
      1. Variáveis de decisão para cada `(curso, disciplina)`, com domínio nos slots livres.  
      2. Restrições para evitar dois exames ao mesmo tempo para um mesmo aluno.  
      3. Booleanos para contar quantos exames cada aluno tem por dia (máximo 3).  
      4. Sincronização de disciplinas entre cursos que compartilham livre.  
      5. Objetivo: minimizar o último slot ocupado.  
    - Resolve o modelo e devolve `exam_schedule[curso] = [lista de disciplinas para cada slot]`.  
  - `src/excel_exporter.py`  
    - Recebe os dados resultantes do modelo (`exam_schedule`), o JSON externo `exams_in_class` (para marcar exames já em sala), e escreve planilhas `.xlsx` em `planilhas/<curso>.xlsx` usando `xlsxwriter`.  
    - Formata colunas, cabeçalhos de dia e horários, insere “1(<disciplina>)” onde há exame em aula, e lista as disciplinas remanescentes conforme alocado pelo CP-SAT.

---

## 2. Pré-requisitos e execução

### 2.1. Pré-requisitos
- **Python 3.13.3**
    - Verifique a versão do seu python com o comando `python --version`

1. Abra o **Prompt de Comando**  na raiz do projeto.
2. Crie e ative o ambiente virtual:
    ```powershell
    python -m venv .venv

    # Windows:
    .venv\Scripts\activate

    # Linux/macOS
    source .venv/bin/activate
    ```

3. Instale as dependências:
    ```powershell
    pip install -r requirements.txt
    ```

### 2.4. Executar a aplicação
1. Certifique-se de que os arquivos JSON brutos estejam na pasta `dados/`, por exemplo:
   - `dados/Horarios.json`
   - `dados/Dias.json`
   - (opcionais, se já existirem: `dados/AlunosEmRecuperacao.json`, `dados/ExamesEmAula.json`)

2. Na raiz do projeto (onde está a pasta `src/`), execute:  
   ```bash
   python -m src.app
   ```  
   ou  
   ```bash
   python src/app.py
   ```

    3. Um menu aparecerá no terminal:  
    ```bash
    1 → Construir AlunosEmRecuperacao.json (GUI)
    2 → Agendar Exames em Sala (GUI)
    3 → Construir planilhas de horário (Excel)
    ```

