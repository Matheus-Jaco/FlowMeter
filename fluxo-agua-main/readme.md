Roda na tua máquina amanhã:

1º Instala o python
2º Descompacta
3º Abre o projeto no VSCODE
4º Abre no terminal o projeto também
5º No terminal usa o comando: source venv/Scripts/activate
6º Dá um enter
7º No terminal, usa o comando: pip install -r requeriments.txt
8º ainda no terminal usa o comando py manage.py runserver

Cada leitura é salva separadamente em FluxoAgua (create não tenta atualizar nada).
Cálculos de consumo diário/mensal são feitos via agregação (Sum) das leituras do dia/mês, sem sobrescrever outros registros.
Não precisa mais do modelo ConsumoDiario para armazenar soma, mas você pode manter se quiser cache ou histórico rápido — mas não obrigatório.
Com isso, sensor 1 e sensor 2 nunca se confundem, mesmo que enviem ao mesmo tempo.