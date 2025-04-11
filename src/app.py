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
            # 识别修改者
            key_id = blockchain.identify_key_owner(private_key)
            response = {
                'message': '区块已成功修改',
                'block': blockchain.chain[data['index']].to_dict(),
                'modified_by': key_id,
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
    """获取区块链的默认公钥和私钥（在实际应用中，私钥应该保密）"""
    response = {
        'public_key': blockchain.get_public_key(),
        'private_key': blockchain.get_private_key(),  # 实际应用中不应暴露私钥
        'message': '警告：在生产环境中，私钥应保密并安全存储，不应直接返回给客户端！'
    }
    return jsonify(response), 200

@app.route('/generate-key-pair', methods=['POST'])
def generate_key_pair():
    """生成新的密钥对"""
    data = request.get_json() or {}
    description = data.get('description', '')
    key_pair = blockchain.generate_key_pair(description)
    
    response = {
        'message': '新密钥对已生成',
        'key_pair': key_pair
    }
    return jsonify(response), 201

@app.route('/key-pairs', methods=['GET'])
def get_all_key_pairs():
    """获取所有密钥对的信息（不包含私钥）"""
    key_pairs = blockchain.get_all_key_pairs()
    response = {
        'key_pairs': key_pairs
    }
    return jsonify(response), 200

@app.route('/block-history/<int:index>', methods=['GET'])
def get_block_history(index):
    """获取特定区块的修改历史"""
    try:
        if index < 0 or index >= len(blockchain.chain):
            return jsonify({'message': '区块索引超出范围!'}), 400
            
        block = blockchain.chain[index]
        response = {
            'block_index': index,
            'modification_history': block.modification_history
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'message': f'获取修改历史时发生错误: {str(e)}'}), 500

@app.route('/identify-key-owner', methods=['POST'])
def identify_key_owner():
    """识别私钥持有者"""
    data = request.get_json()
    if not data or 'private_key' not in data:
        return jsonify({'message': '请提供私钥!'}), 400
    
    private_key = data.get('private_key')
    key_id = blockchain.identify_key_owner(private_key)
    
    if key_id:
        response = {
            'message': '已识别密钥所有者',
            'key_id': key_id
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': '无法识别密钥所有者，密钥可能无效'}), 404

@app.route('/get-key-by-id', methods=['POST'])
def get_key_by_id():
    """根据ID获取密钥信息"""
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({'message': '请提供密钥ID!'}), 400
    
    key_id = data.get('id')
    
    # 获取所有密钥信息
    key_pairs = blockchain.chameleon_hash.key_pairs
    
    if key_id not in key_pairs:
        return jsonify({'message': f'找不到ID为 {key_id} 的密钥!'}), 404
    
    # 返回密钥信息（包括私钥）
    # 注意：实际生产环境应当考虑安全限制，此处为演示使用
    response = {
        'id': key_id,
        'private_key': key_pairs[key_id]['private_key'],
        'public_key': key_pairs[key_id]['public_key'],
        'description': key_pairs[key_id]['description']
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)