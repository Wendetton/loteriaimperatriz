import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func

# Inicialização do Flask
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'loteria-imperatriz-2025-key')

# Configuração CORS
CORS(app)

# Configuração do banco de dados
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///loteria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do banco
db = SQLAlchemy(app)

# Modelos do banco de dados
class Movimentacao(db.Model):
    """Modelo para registrar movimentações individuais (suprimentos e sangrias)"""
    __tablename__ = 'movimentacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, index=True)
    caixa = db.Column(db.Integer, nullable=False, index=True)  # 1-6
    tipo = db.Column(db.String(20), nullable=False)  # 'suprimento' ou 'sangria'
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    ordem = db.Column(db.Integer, default=1)  # Para ordenar movimentações do mesmo tipo
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.strftime('%Y-%m-%d'),
            'caixa': self.caixa,
            'tipo': self.tipo,
            'descricao': self.descricao,
            'valor': float(self.valor),
            'ordem': self.ordem,
            'timestamp': self.timestamp.isoformat()
        }

class Fechamento(db.Model):
    """Modelo para registrar fechamento diário de cada caixa"""
    __tablename__ = 'fechamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, index=True)
    caixa = db.Column(db.Integer, nullable=False, index=True)  # 1-6
    saldo_inicial = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    valor_maquina = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    observacoes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraint para garantir um fechamento por caixa por dia
    __table_args__ = (db.UniqueConstraint('data', 'caixa', name='unique_fechamento_diario'),)
    
    @property
    def total_suprimentos(self):
        """Calcula total de suprimentos do dia"""
        movs = Movimentacao.query.filter_by(
            data=self.data, 
            caixa=self.caixa, 
            tipo='suprimento'
        ).all()
        return sum(float(mov.valor) for mov in movs)
    
    @property
    def total_sangrias(self):
        """Calcula total de sangrias do dia"""
        movs = Movimentacao.query.filter_by(
            data=self.data, 
            caixa=self.caixa, 
            tipo='sangria'
        ).all()
        return sum(float(mov.valor) for mov in movs)
    
    @property
    def saldo_calculado(self):
        """Calcula saldo baseado em: saldo_inicial + suprimentos - sangrias"""
        return float(self.saldo_inicial) + self.total_suprimentos - self.total_sangrias
    
    @property
    def diferenca(self):
        """Calcula diferença entre valor da máquina e saldo calculado"""
        return float(self.valor_maquina) - self.saldo_calculado
    
    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.strftime('%Y-%m-%d'),
            'caixa': self.caixa,
            'saldo_inicial': float(self.saldo_inicial),
            'valor_maquina': float(self.valor_maquina),
            'total_suprimentos': self.total_suprimentos,
            'total_sangrias': self.total_sangrias,
            'saldo_calculado': self.saldo_calculado,
            'diferenca': self.diferenca,
            'observacoes': self.observacoes,
            'timestamp': self.timestamp.isoformat()
        }

# Rotas da API
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Retorna dados do dashboard com resumo de todos os caixas"""
    try:
        data_hoje = date.today()
        
        # Buscar fechamentos de hoje para todos os caixas
        fechamentos = Fechamento.query.filter_by(data=data_hoje).all()
        
        # Criar resumo por caixa
        resumo_caixas = []
        for caixa_num in range(1, 7):
            fechamento = next((f for f in fechamentos if f.caixa == caixa_num), None)
            
            if fechamento:
                resumo = fechamento.to_dict()
                resumo['status'] = 'OK' if abs(fechamento.diferenca) <= 10 else 'VERIFICAR'
            else:
                resumo = {
                    'caixa': caixa_num,
                    'data': data_hoje.strftime('%Y-%m-%d'),
                    'saldo_inicial': 0,
                    'valor_maquina': 0,
                    'total_suprimentos': 0,
                    'total_sangrias': 0,
                    'saldo_calculado': 0,
                    'diferenca': 0,
                    'status': 'PENDENTE'
                }
            
            resumo_caixas.append(resumo)
        
        # Calcular totais gerais
        total_suprimentos = sum(c['total_suprimentos'] for c in resumo_caixas)
        total_sangrias = sum(c['total_sangrias'] for c in resumo_caixas)
        saldo_total = sum(c['saldo_calculado'] for c in resumo_caixas)
        caixas_com_problema = len([c for c in resumo_caixas if c['status'] == 'VERIFICAR'])
        
        return jsonify({
            'success': True,
            'data': {
                'data': data_hoje.strftime('%Y-%m-%d'),
                'caixas': resumo_caixas,
                'totais': {
                    'suprimentos': total_suprimentos,
                    'sangrias': total_sangrias,
                    'saldo_total': saldo_total,
                    'caixas_com_problema': caixas_com_problema
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/caixa/<int:caixa_num>', methods=['GET'])
def obter_caixa(caixa_num):
    """Retorna dados de um caixa específico para uma data"""
    try:
        data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
        data_consulta = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Buscar fechamento do dia
        fechamento = Fechamento.query.filter_by(data=data_consulta, caixa=caixa_num).first()
        
        # Buscar movimentações do dia
        suprimentos = Movimentacao.query.filter_by(
            data=data_consulta, 
            caixa=caixa_num, 
            tipo='suprimento'
        ).order_by(Movimentacao.ordem).all()
        
        sangrias = Movimentacao.query.filter_by(
            data=data_consulta, 
            caixa=caixa_num, 
            tipo='sangria'
        ).order_by(Movimentacao.ordem).all()
        
        # Buscar saldo inicial (valor da máquina do dia anterior)
        data_anterior = data_consulta.replace(day=data_consulta.day - 1) if data_consulta.day > 1 else data_consulta
        fechamento_anterior = Fechamento.query.filter_by(
            data=data_anterior, 
            caixa=caixa_num
        ).first()
        
        saldo_inicial = float(fechamento_anterior.valor_maquina) if fechamento_anterior else 500.0
        
        return jsonify({
            'success': True,
            'data': {
                'caixa': caixa_num,
                'data': data_str,
                'saldo_inicial': saldo_inicial,
                'fechamento': fechamento.to_dict() if fechamento else None,
                'suprimentos': [s.to_dict() for s in suprimentos],
                'sangrias': [s.to_dict() for s in sangrias]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/caixa/<int:caixa_num>/movimentacao', methods=['POST'])
def adicionar_movimentacao(caixa_num):
    """Adiciona uma nova movimentação (suprimento ou sangria)"""
    try:
        dados = request.get_json()
        
        data_mov = datetime.strptime(dados['data'], '%Y-%m-%d').date()
        
        # Determinar próxima ordem para o tipo
        ultima_ordem = db.session.query(func.max(Movimentacao.ordem)).filter_by(
            data=data_mov,
            caixa=caixa_num,
            tipo=dados['tipo']
        ).scalar() or 0
        
        movimentacao = Movimentacao(
            data=data_mov,
            caixa=caixa_num,
            tipo=dados['tipo'],  # 'suprimento' ou 'sangria'
            descricao=dados['descricao'],
            valor=dados['valor'],
            ordem=ultima_ordem + 1
        )
        
        db.session.add(movimentacao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': movimentacao.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/caixa/<int:caixa_num>/movimentacao/<int:mov_id>', methods=['DELETE'])
def remover_movimentacao(caixa_num, mov_id):
    """Remove uma movimentação"""
    try:
        movimentacao = Movimentacao.query.get_or_404(mov_id)
        
        db.session.delete(movimentacao)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/caixa/<int:caixa_num>/fechamento', methods=['POST'])
def salvar_fechamento(caixa_num):
    """Salva ou atualiza fechamento de um caixa"""
    try:
        dados = request.get_json()
        
        data_fech = datetime.strptime(dados['data'], '%Y-%m-%d').date()
        
        # Buscar fechamento existente ou criar novo
        fechamento = Fechamento.query.filter_by(data=data_fech, caixa=caixa_num).first()
        
        if not fechamento:
            fechamento = Fechamento(data=data_fech, caixa=caixa_num)
        
        fechamento.saldo_inicial = dados.get('saldo_inicial', fechamento.saldo_inicial)
        fechamento.valor_maquina = dados.get('valor_maquina', fechamento.valor_maquina)
        fechamento.observacoes = dados.get('observacoes', fechamento.observacoes)
        
        if not fechamento.id:
            db.session.add(fechamento)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': fechamento.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/central', methods=['GET'])
def caixa_central():
    """Retorna dados consolidados do caixa central"""
    try:
        data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
        data_consulta = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Buscar dados de todos os caixas para a data
        fechamentos = Fechamento.query.filter_by(data=data_consulta).all()
        
        dados_caixas = []
        total_suprimentos = 0
        total_sangrias = 0
        total_saldo = 0
        caixas_com_problema = 0
        
        for caixa_num in range(1, 7):
            fechamento = next((f for f in fechamentos if f.caixa == caixa_num), None)
            
            if fechamento:
                dados = fechamento.to_dict()
                dados['status'] = 'OK' if abs(fechamento.diferenca) <= 10 else 'VERIFICAR'
                
                if dados['status'] == 'VERIFICAR':
                    caixas_com_problema += 1
                
                total_suprimentos += dados['total_suprimentos']
                total_sangrias += dados['total_sangrias']
                total_saldo += dados['saldo_calculado']
            else:
                dados = {
                    'caixa': caixa_num,
                    'data': data_str,
                    'saldo_inicial': 0,
                    'valor_maquina': 0,
                    'total_suprimentos': 0,
                    'total_sangrias': 0,
                    'saldo_calculado': 0,
                    'diferenca': 0,
                    'status': 'PENDENTE'
                }
            
            dados_caixas.append(dados)
        
        return jsonify({
            'success': True,
            'data': {
                'data': data_str,
                'caixas': dados_caixas,
                'consolidacao': {
                    'total_suprimentos': total_suprimentos,
                    'total_sangrias': total_sangrias,
                    'saldo_total': total_saldo,
                    'caixas_com_problema': caixas_com_problema,
                    'maior_diferenca': max([abs(c['diferenca']) for c in dados_caixas], default=0)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/historico', methods=['GET'])
def historico():
    """Retorna histórico de fechamentos por período"""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        caixa_num = request.args.get('caixa', type=int)
        
        query = Fechamento.query
        
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            query = query.filter(Fechamento.data >= data_inicio)
        
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            query = query.filter(Fechamento.data <= data_fim)
        
        if caixa_num:
            query = query.filter(Fechamento.caixa == caixa_num)
        
        fechamentos = query.order_by(Fechamento.data.desc(), Fechamento.caixa).all()
        
        return jsonify({
            'success': True,
            'data': [f.to_dict() for f in fechamentos]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Rota para servir arquivos estáticos
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Inicialização do banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

