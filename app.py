import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
CORS(app)

# Config DB
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="hotel_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "hotel_db"),
    autocommit=False,
    use_pure=True
)

def get_db_connection():
    return db_pool.get_connection()



# LOGINS

@app.route('/api/v1/login/cliente', methods=['POST']) #login do cliente
def login_cliente():
    data = request.get_json() or {}
    email = data.get('email')
    senha = data.get('senha')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute( # select para buscar o cliente com base no email e senha fornecidos
            "SELECT idCliente, NomeCliente, EmailCliente FROM Cliente WHERE EmailCliente = %s AND SenhaCliente = %s",
            (email, senha)
        )
        usuario = cursor.fetchone()
        
        if not usuario:
            return jsonify({"sucesso": False, "mensagem": "Credenciais inválidas."}), 401

        return jsonify({"sucesso": True, "mensagem": "Login realizado com sucesso", "usuario": usuario})
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/v1/login/colaborador', methods=['POST']) #login do colaborador
def login_colaborador():
    data = request.get_json() or {}
    login = data.get('login')
    senha = data.get('senha')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT idFuncionario, idLogin, NomeFuncionario, FuncaoFuncionario FROM Funcionario WHERE idLogin = %s AND SenhaFuncionario = %s",
            (login, senha)
        )
        funcionario = cursor.fetchone()

        if not funcionario:
            return jsonify({"sucesso": False, "mensagem": "Credenciais inválidas."}), 401

        return jsonify({"sucesso": True, "mensagem": "Login efetuado", "funcionario": funcionario})
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



# GERENCIA


# Tipos de Quarto
@app.route('/api/v1/tipos_quarto', methods=['GET', 'POST'])
def tipos_quarto():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            cursor.execute("SELECT * FROM Tipo_Quarto") # seleciona todos os tipos de quarto cadastrados no banco de dados
            rows = cursor.fetchall()
            return jsonify({"sucesso": True, "dados": rows})

        elif request.method == 'POST': # adiciona um novo tipo de quarto ao banco de dados
            data = request.get_json() or {}
            cursor.execute(
                "INSERT INTO Tipo_Quarto (nome_tipoQuarto, valor_base, limite_adultos, limite_criancas) VALUES (%s, %s, %s, %s)",
                (data.get('nome_tipoQuarto'), data.get('valor_base'), data.get('limite_adultos'), data.get('limite_criancas'))
            )
            conn.commit()
            return jsonify({"sucesso": True, "idTipoQuarto": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/v1/tipos_quarto/<int:id_tipo>', methods=['PUT']) # atualiza as informações de um tipo de quarto específico no banco de dados
def atualizar_tipo_quarto(id_tipo):
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Tipo_Quarto SET nome_tipoQuarto = %s, valor_base = %s, limite_adultos = %s, limite_criancas = %s WHERE idTipoQuarto = %s",
            (data.get('nome_tipoQuarto'), data.get('valor_base'), data.get('limite_adultos'), data.get('limite_criancas'), id_tipo)
        )
        conn.commit()
        return jsonify({"sucesso": True, "mensagem": "Tipo de quarto atualizado com sucesso."})
    except Exception as e:
        conn.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Quartos 
@app.route('/api/v1/quartos', methods=['GET', 'POST'])
def quartos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            # Usa LEFT JOIN e garante o idTipo_Quarto (com underline) na tabela Tipo_Quarto
            query = """
                SELECT 
                    q.idQuarto, 
                    q.num_quarto, 
                    q.statusQuarto, 
                    q.idTipoQuarto,
                    t.nome_tipoQuarto, 
                    t.valor_base 
                FROM Quarto q
                LEFT JOIN Tipo_Quarto t ON q.idTipoQuarto = t.idTipo_Quarto
            """
            cursor.execute(query)
            return jsonify({"sucesso": True, "dados": cursor.fetchall()})

        elif request.method == 'POST':
            data = request.get_json() or {}
            cursor.execute(
                "INSERT INTO Quarto (num_quarto, idTipoQuarto, statusQuarto) VALUES (%s, %s, %s)",
                (data.get('num_quarto'), data.get('idTipoQuarto'), data.get('statusQuarto', 'DISPONIVEL'))
            )
            conn.commit()
            return jsonify({"sucesso": True, "idQuarto": cursor.lastrowid}), 201

    except Exception as e:
        conn.rollback()
        print(f"Erro interno na rota /quartos: {e}")
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/v1/quartos/<int:id_quarto>', methods=['PUT']) #atualiza as informações de um quarto específico no banco de dados, incluindo seu número, tipo e status
def atualizar_quarto(id_quarto):
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Quarto SET num_quarto = %s, idTipoQuarto = %s, statusQuarto = %s WHERE idQuarto = %s",
            (data.get('num_quarto'), data.get('idTipoQuarto'), data.get('statusQuarto'), id_quarto)
        )
        conn.commit()
        return jsonify({"sucesso": True, "mensagem": "Quarto atualizado com sucesso."})
    except Exception as e:
        conn.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Salas de Conferência
@app.route('/api/v1/salas', methods=['GET', 'POST']) 
def salas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET': # retorna todas as salas de conferência cadastradas no banco de dados
            cursor.execute("SELECT * FROM Sala_Conferencia")
            return jsonify({"sucesso": True, "dados": cursor.fetchall()})

        elif request.method == 'POST': # adiciona uma nova sala de conferência ao banco de dados
            data = request.get_json() or {}
            cursor.execute(
                "INSERT INTO Sala_Conferencia (nome_salaConferencia, capacidade_maxima, valor_turno, statusSala) VALUES (%s, %s, %s, %s)",
                (data.get('nome_salaConferencia'), data.get('capacidade_maxima'), data.get('valor_turno'), data.get('statusSala', 'DISPONIVEL'))
            )
            conn.commit()
            return jsonify({"sucesso": True, "idSala": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/v1/salas/<int:id_sala>', methods=['PUT']) # atualiza as informações de uma sala de conferência específica no banco de dados
def atualizar_sala(id_sala):
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Sala_Conferencia SET nome_salaConferencia = %s, capacidade_maxima = %s, valor_turno = %s, statusSala = %s WHERE idSala_Conferencia = %s",
            (data.get('nome_salaConferencia'), data.get('capacidade_maxima'), data.get('valor_turno'), data.get('statusSala'), id_sala)
        )
        conn.commit()
        return jsonify({"sucesso": True, "mensagem": "Sala atualizada com sucesso."})
    except Exception as e:
        conn.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Faturamento (Consulta 1)
@app.route('/api/v1/faturamento', methods=['GET'])
def faturamento():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Calcula o Faturamento de Hospedagem (Diárias + Consumo)
        query_hosp = """
            SELECT 
                COUNT(idReserva_Hospedagem) AS total_reservas,
                COALESCE(SUM(valor_Reserva), 0) AS total_diarias,
                COALESCE(SUM(valor_Consumacao), 0) AS total_consumo,
                COALESCE(SUM(valor_Reserva + valor_Consumacao), 0) AS faturamento_hospedagem
            FROM Reserva_Hospedagem
            WHERE status != 'CANCELADO'
        """
        params_hosp = []
        if data_inicio and data_fim:
            query_hosp += " AND data_CheckIn <= %s AND data_CheckOut >= %s"
            params_hosp.extend([data_fim, data_inicio])

        cursor.execute(query_hosp, tuple(params_hosp))
        res_hosp = cursor.fetchone()

        # 2. Calcula o Faturamento de Conferências / Aluguel de Salas
        # (Nota: Se o nome da sua tabela de conferências for diferente, ajuste 'Aluguel_Conferencia' e a coluna de valor)
        query_conf = """
            SELECT 
                COALESCE(SUM(valor), 0) AS faturamento_conferencia
            FROM Aluguel_Conferencia
            WHERE status != 'CANCELADO'
        """
        params_conf = []
        if data_inicio and data_fim:
            # Ajuste os nomes das colunas de data da conferência se forem diferentes (ex: data_inicio, data_fim)
            query_conf += " AND data_inicio <= %s AND data_fim >= %s"
            params_conf.extend([data_fim, data_inicio])

        try:
            cursor.execute(query_conf, tuple(params_conf))
            res_conf = cursor.fetchone()
            faturamento_conferencia = float(res_conf['faturamento_conferencia'] or 0)
        except Exception:
            # Caso a tabela de conferência ainda não exista no banco, assume 0 para não quebrar
            faturamento_conferencia = 0.00

        # 3. Consolida os valores
        faturamento_hospedagem = float(res_hosp['faturamento_hospedagem'] or 0)
        faturamento_total = faturamento_hospedagem + faturamento_conferencia

        # Monta o objeto de relatório esperado pelo front-end
        resultado = {
            "total_reservas": res_hosp['total_reservas'],
            "total_diarias": res_hosp['total_diarias'],
            "total_consumo": res_hosp['total_consumo'],
            "faturamento_hospedagem": faturamento_hospedagem,
            "faturamento_conferencia": faturamento_conferencia,
            "faturamento_total": faturamento_total
        }
        
        return jsonify({
            "sucesso": True, 
            "periodo": {"data_inicio": data_inicio, "data_fim": data_fim}, 
            "relatorio": resultado
        })
    except Exception as e:
        print(f"ERRO NO FATURAMENTO: {e}")
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

        
# 3. CLIENTE / RESERVAS


# Criar Reserva (TRANSAÇÃO 1)
@app.route('/api/v1/reservas', methods=['POST'])
def criar_reserva():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        dados = request.get_json() or {}

        id_cliente = dados.get('idCliente')
        id_tipo_quarto = dados.get('idTipoQuarto')
        data_checkin = dados.get('data_checkin')
        data_checkout = dados.get('data_checkout')
        qnt_adultos = dados.get('qnt_adultos', 1)
        qnt_criancas = dados.get('qnt_criancas', 0)
        cafe_manha = 1 if dados.get('cafe_manha') else 0

        # 1. Busca o preço base do tipo de quarto (ajuste o nome da coluna se necessário, ex: valor_base)
        cursor.execute("SELECT valor_base FROM Tipo_Quarto WHERE idTipo_Quarto = %s", (id_tipo_quarto,))
        tipo_quarto = cursor.fetchone()
        
        if not tipo_quarto:
            return jsonify({"sucesso": False, "mensagem": "Tipo de quarto não encontrado."}), 404

        valor_base = float(tipo_quarto.get('valor_base', 0))

        # 2. Calcula a quantidade de dias entre o check-in e o check-out
        d1 = datetime.strptime(data_checkin, '%Y-%m-%d')
        d2 = datetime.strptime(data_checkout, '%Y-%m-%d')
        dias = max(1, (d2 - d1).days)
        
        # 3. Calcula o valor total das diárias
        valor_reserva = valor_base * dias

        # 4. Insere a reserva salvando o valor calculado e o status inicial 'RESERVADO'
        query = """
            INSERT INTO Reserva_Hospedagem 
                (idCliente, idTipoQuarto, data_CheckIn, data_CheckOut, qnt_adultos, qnt_criancas, cafe_manha, valor_Reserva, status)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, 'RESERVADO')
        """
        valores = (id_cliente, id_tipo_quarto, data_checkin, data_checkout, qnt_adultos, qnt_criancas, cafe_manha, valor_reserva)

        cursor.execute(query, valores)
        conn.commit()

        return jsonify({
            "sucesso": True, 
            "mensagem": "Reserva realizada com sucesso!", 
            "valor_reserva": valor_reserva
        }), 201

    except Exception as e:
        conn.rollback()
        print(f"ERRO AO CRIAR RESERVA: {e}") 
        return jsonify({"sucesso": False, "mensagem": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

#buscar reserva por id
@app.route('/api/v1/reservas/<int:id_reserva>', methods=['GET'])
def buscar_reserva_unica(id_reserva):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Busca a reserva e cruza com a tabela Tipo_Quarto para pegar o nome
        query = """
            SELECT r.idReserva_Hospedagem, r.idTipoQuarto, t.nome_tipoQuarto 
            FROM Reserva_Hospedagem r
            LEFT JOIN Tipo_Quarto t ON r.idTipoQuarto = t.idTipo_Quarto
            WHERE r.idReserva_Hospedagem = %s
        """
        cursor.execute(query, (id_reserva,))
        reserva = cursor.fetchone()
        
        if reserva:
            return jsonify({"sucesso": True, "reserva": reserva}), 200
        else:
            return jsonify({"sucesso": False, "mensagem": "Reserva não encontrada"}), 404
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Cancelar Reserva (TRANSAÇÃO 2)
@app.route('/api/v1/reservas/<int:id_reserva>/cancelar', methods=['PATCH', 'PUT'])
def cancelar_reserva(id_reserva):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Atualiza o status da reserva para CANCELADO
        query = "UPDATE Reserva_Hospedagem SET status = 'CANCELADO' WHERE idReserva_Hospedagem = %s"
        cursor.execute(query, (id_reserva,))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"sucesso": True, "mensagem": "Reserva cancelada com sucesso!"}), 200
        else:
            return jsonify({"sucesso": False, "mensagem": "Reserva não encontrada."}), 404

    except Exception as e:
        conn.rollback()
        print(f"Erro ao cancelar reserva {id_reserva}: {e}")
        return jsonify({"sucesso": False, "mensagem": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Consultar Reservas do Cliente (CONSULTA 2)
@app.route('/api/v1/clientes/<int:id_cliente>/reservas', methods=['GET'])
def listar_reservas_cliente(id_cliente):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Note o JOIN: r.idTipoQuarto = t.idTipo_Quarto
        query = """
            SELECT 
                r.idReserva_Hospedagem,
                r.data_CheckIn,
                r.data_CheckOut,
                r.status,
                t.nome_tipoQuarto
            FROM Reserva_Hospedagem r
            LEFT JOIN Tipo_Quarto t ON r.idTipoQuarto = t.idTipo_Quarto
            WHERE r.idCliente = %s
        """
        cursor.execute(query, (id_cliente,))
        reservas = cursor.fetchall()

        # Converte objetos 'date' para string 'YYYY-MM-DD' para o jsonify
        for res in reservas:
            if res.get('data_CheckIn'):
                res['data_CheckIn'] = str(res['data_CheckIn'])
            if res.get('data_CheckOut'):
                res['data_CheckOut'] = str(res['data_CheckOut'])

        return jsonify({"sucesso": True, "dados": reservas}), 200

    except Exception as e:
        print(f"ERRO AO BUSCAR RESERVAS DO CLIENTE {id_cliente}: {e}")
        return jsonify({"sucesso": False, "mensagem": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# 4. RECEPÇÃO

# Mapa de Ocupação (CONSULTA 3)
@app.route('/api/v1/mapa', methods=['GET'])
def mapa_ocupacao():
    data_filtro = request.args.get('data_filtro')
    if not data_filtro:
        return jsonify({"sucesso": False, "mensagem": "Parâmetro data_filtro é obrigatório."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Corrigido para t.idTipo_Quarto (com underline) e acrescentado previsao de checkout
        query = """ 
            SELECT 
                q.idQuarto, 
                q.num_quarto, 
                q.statusQuarto,
                t.nome_tipoQuarto,
                r.idReserva_Hospedagem,
                r.valor_Reserva,
                r.valor_Consumacao,
                r.data_CheckOut AS previsao_checkout,
                c.NomeCliente AS nome_hospede,
                r.status AS statusReserva
            FROM Quarto q
            LEFT JOIN Tipo_Quarto t ON q.idTipoQuarto = t.idTipo_Quarto
            LEFT JOIN Reserva_Hospedagem r ON q.idQuarto = r.idQuarto 
                 AND %s BETWEEN r.data_CheckIn AND r.data_CheckOut 
                 AND r.status = 'HOSPEDADO'
            LEFT JOIN Cliente c ON r.idCliente = c.idCliente
            ORDER BY q.num_quarto ASC
        """
        cursor.execute(query, (data_filtro,))
        return jsonify({"sucesso": True, "data_filtrada": data_filtro, "mapa": cursor.fetchall()})
    except Exception as e:
        print(f"Erro ao carregar mapa: {e}")
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Realizar Check-in 
@app.route('/api/v1/checkin', methods=['POST']) # realiza o check-in de uma reserva, associando um quarto específico à reserva e alterando o status da reserva para "HOSPEDADO" e o status do quarto para "OCUPADO"
def realizar_checkin():
    data = request.get_json() or {}
    id_reserva = data.get('idReserva')
    id_quarto = data.get('idQuarto')

    if not id_reserva or not id_quarto:
        return jsonify({"sucesso": False, "mensagem": "idReserva e idQuarto são obrigatórios."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar reserva válida
        cursor.execute(
            "SELECT * FROM Reserva_Hospedagem WHERE idReserva_Hospedagem = %s AND status = 'RESERVADO'",
            (id_reserva,)
        )
        reserva = cursor.fetchone()

        if not reserva:
            return jsonify({"sucesso": False, "mensagem": "Reserva não encontrada ou inválida para check-in."}), 400

        # Atualiza a reserva atrelando o quarto e alterando status
        cursor.execute(
            "UPDATE Reserva_Hospedagem SET idQuarto = %s, status = 'HOSPEDADO' WHERE idReserva_Hospedagem = %s",
            (id_quarto, id_reserva)
        )

        # Atualiza o quarto para OCUPADO
        cursor.execute(
            "UPDATE Quarto SET statusQuarto = 'OCUPADO' WHERE idQuarto = %s",
            (id_quarto,)
        )

        conn.commit()
        return jsonify({"sucesso": True, "mensagem": "Check-in concluído com sucesso!", "idReserva": id_reserva, "idQuarto": id_quarto})
    except Exception as e:
        conn.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



# Realizar Check-out 
@app.route('/api/v1/checkout', methods=['POST'])
def realizar_checkout():
    data = request.get_json() or {}
    id_reserva = data.get('idReserva')
    valor_consumo = float(data.get('valor_consumacao', 0.00))

    if not id_reserva:
        return jsonify({"sucesso": False, "mensagem": "idReserva é obrigatório."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Busca a reserva hospedada
        cursor.execute(
            "SELECT idQuarto, valor_Reserva, valor_Consumacao FROM Reserva_Hospedagem WHERE idReserva_Hospedagem = %s AND status = 'HOSPEDADO'",
            (id_reserva,)
        )
        reserva = cursor.fetchone()

        if not reserva:
            return jsonify({"sucesso": False, "mensagem": "Reserva não encontrada ou não está em andamento."}), 400

        id_quarto = reserva['idQuarto']
        
        # Pega o consumo anterior do banco se houver, somando com o novo se enviado
        consumo_atual = float(reserva.get('valor_Consumacao') or 0.00) + valor_consumo
        valor_diarias = float(reserva.get('valor_Reserva') or 0.00)
        total_pagar = valor_diarias + consumo_atual

        # Finaliza reserva atualizando status e mantendo/atualizando o consumo
        cursor.execute(
            "UPDATE Reserva_Hospedagem SET status = 'FINALIZADO', valor_Consumacao = %s WHERE idReserva_Hospedagem = %s",
            (consumo_atual, id_reserva)
        )

        # Libera o quarto associado
        if id_quarto:
            cursor.execute("UPDATE Quarto SET statusQuarto = 'DISPONIVEL' WHERE idQuarto = %s", (id_quarto,))

        conn.commit()
        return jsonify({
            "sucesso": True,
            "mensagem": "Check-out realizado com sucesso!",
            "idReserva": id_reserva,
            "valor_diarias": valor_diarias,
            "valor_consumo": consumo_atual,
            "total_pago": total_pagar
        })
    except Exception as e:
        conn.rollback()
        print(f"ERRO NO CHECKOUT: {e}")
        return jsonify({"sucesso": False, "erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# INICIALIZAÇÃO DO SERVIDOR

if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", 3000))
    print(f"Servidor Flask rodando em http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)