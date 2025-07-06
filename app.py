import os
import logging
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do Flask
app = Flask(__name__, static_folder='static')

# Configuração de segurança
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'loteria-imperatriz-secret-key-2025')

# Configuração CORS - permitir todas as origens
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuração do banco de dados
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Corrigir URL do PostgreSQL se necessário
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Usar SQLite para desenvolvimento local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loteria.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

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
        try:
            movs = Movimentacao.query.filter_by(
                data=self.data, 
                caixa=self.caixa, 
                tipo='suprimento'
            ).all()
            return sum(float(mov.valor) for mov in movs)
        except:
            return 0.0
    
    @property
    def total_sangrias(self):
        """Calcula total de sangrias do dia"""
        try:
            movs = Movimentacao.query.filter_by(
                data=self.data, 
                caixa=self.caixa, 
                tipo='sangria'
            ).all()
            return sum(float(mov.valor) for mov in movs)
        except:
            return 0.0
    
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
            'observacoes': self.observacoes or '',
            'timestamp': self.timestamp.isoformat()
        }

# Rota de health check
@app.route('/health')
def health_check():
    """Health check para verificar se a aplicação está funcionando"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.engine else 'disconnected'
    })

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
        logger.error(f"Erro no dashboard: {str(e)}")
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
        from datetime import timedelta
        data_anterior = data_consulta - timedelta(days=1)
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
        logger.error(f"Erro ao obter caixa {caixa_num}: {str(e)}")
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
        logger.error(f"Erro ao adicionar movimentação: {str(e)}")
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
        logger.error(f"Erro ao remover movimentação: {str(e)}")
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
        logger.error(f"Erro ao salvar fechamento: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Rota para servir arquivos estáticos
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve arquivos estáticos e SPA"""
    try:
        if path and path != "":
            # Verificar se é um arquivo estático
            static_file_path = os.path.join(app.static_folder, path)
            if os.path.exists(static_file_path):
                return send_from_directory(app.static_folder, path)
        
        # Servir index.html para todas as outras rotas (SPA)
        index_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return "Sistema da Loteria Imperatriz - Arquivo index.html não encontrado", 404
    except Exception as e:
        logger.error(f"Erro ao servir arquivo: {str(e)}")
        return f"Erro interno: {str(e)}", 500

# Inicialização do banco de dados
def init_db():
    """Inicializa o banco de dados"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {str(e)}")

# Inicializar banco na importação
init_db()

if __name__ == '__main__':
    # Configuração para deploy
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Iniciando aplicação na porta {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

