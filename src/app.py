from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
from src.blockchain import Blockchain

# 初始化Flask应用
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# 创建区块链实例
blockchain = Blockchain()

@app.route('/', methods=['GET'])
def index():
    """渲染前端页面"""
    return render_template('index.html')

@app.route('/chain', methods=['GET'])
def get_chain():
    """获取完整区块链数据"""
    response = {
        'chain': blockchain.to_dict(),
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/mine', methods=['POST'])
def mine_block():
    """创建一个新区块"""
    data = request.get_json()
    if not data:
        return jsonify({'message': '没有提供数据!'}), 400
    
    # 添加新区块
    block = blockchain.add_block(data)
    
    response = {
        'message': '新区块已添加',
        'block': block.to_dict(),
        'chain_length': len(blockchain.chain)
    }
    return jsonify(response), 201

@app.route('/modify', methods=['POST'])
def modify_block():
    """修改区块链中的数据，需要提供有效的私钥"""
    data = request.get_json()
    if not data or 'index' not in data or 'new_data' not in data:
        return jsonify({'message': '请提供区块索引和新数据!'}), 400
    
    # 检查是否提供了私钥
    private_key = data.get('private_key')
    if not private_key:
        return jsonify({'message': '需要提供有效的私钥才能修改区块!'}), 403
    
    try:
        success = blockchain.modify_block(data['index'], data['new_data'], private_key)
        if success:
            response = {
                'message': '区块已成功修改',
                'block': blockchain.chain[data['index']].to_dict(),
                'chain_valid': blockchain.is_chain_valid()
            }
            return jsonify(response), 200
        else:
            return jsonify({'message': '修改区块失败!'}), 500
    except PermissionError as e:  # 这是Python内置的异常类
        return jsonify({'message': str(e)}), 403
    except IndexError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': f'发生错误: {str(e)}'}), 500

@app.route('/validate', methods=['GET'])
def validate_chain():
    """验证区块链的完整性"""
    is_valid = blockchain.is_chain_valid()
    if is_valid:
        response = {'message': '区块链有效。'}
    else:
        response = {'message': '区块链无效!'}
    
    return jsonify(response), 200

@app.route('/keys', methods=['GET'])
def get_keys():
    """获取区块链的公钥和私钥（在实际应用中，私钥应该保密）"""
    response = {
        'public_key': blockchain.get_public_key(),
        'private_key': blockchain.get_private_key(),  # 实际应用中不应暴露私钥
        'message': '警告：在生产环境中，私钥应保密并安全存储，不应直接返回给客户端！'
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)