import hashlib
import json
import time
from datetime import datetime
from .chameleon_hash import ChameleonHash

class Block:
    def __init__(self, index, timestamp, data, previous_hash='', random_value=None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.random_value = random_value
        self.hash, self.random_value = self._calculate_hash()
        
    def _calculate_hash(self):
        """
        计算区块的哈希值
        使用变色龙哈希函数来允许后续修改
        """
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True).encode()
        
        # 使用变色龙哈希
        chameleon = ChameleonHash()
        hash_value, random_value = chameleon.hash(block_string, self.random_value)
        
        # 返回十六进制格式的哈希值和随机值
        return hash_value.hex(), random_value
    
    def to_dict(self):
        """将区块转换为字典格式"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'random_value': self.random_value
        }

class Blockchain:
    def __init__(self):
        """初始化区块链，创建创世区块"""
        self.chain = []
        self.chameleon_hash = ChameleonHash()
        # 保存数字格式的公钥和私钥
        self.public_key = self.chameleon_hash.export_public_key()
        self.private_key = self.chameleon_hash.export_private_key()
        self.create_genesis_block()
    
    def get_public_key(self):
        """获取区块链的公钥"""
        return self.public_key
    
    def get_private_key(self):
        """获取区块链的私钥 - 注意：在实际应用中应该限制访问"""
        return self.private_key
    
    def create_genesis_block(self):
        """创建创世区块（第一个区块）"""
        genesis_block = Block(0, datetime.now().isoformat(), {"message": "创世区块"}, "0")
        self.chain.append(genesis_block)
        return genesis_block
    
    def get_latest_block(self):
        """获取区块链中的最新区块"""
        return self.chain[-1]
    
    def add_block(self, data):
        """
        添加新区块到区块链
        params:
            data: 区块中要存储的数据
        """
        latest_block = self.get_latest_block()
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=datetime.now().isoformat(),
            data=data,
            previous_hash=latest_block.hash
        )
        self.chain.append(new_block)
        return new_block
    
    def is_chain_valid(self):
        """
        验证区块链的完整性
        检查每个区块的哈希值是否与前一个区块相链接
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # 验证当前区块哈希值是否正确
            block_string = json.dumps({
                'index': current_block.index,
                'timestamp': current_block.timestamp,
                'data': current_block.data,
                'previous_hash': current_block.previous_hash
            }, sort_keys=True).encode()
            
            chameleon = ChameleonHash()
            current_hash, _ = chameleon.hash(block_string, current_block.random_value)
            if current_hash.hex() != current_block.hash:
                return False
            
            # 验证前一个区块的哈希是否与当前区块中存储的前一个哈希匹配
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def modify_block(self, block_index, new_data, private_key=None):
        """
        修改区块链中的数据
        params:
            block_index: 要修改的区块索引
            new_data: 新的数据
            private_key: 进行操作的私钥，如果不提供则使用默认私钥
        """
        if block_index < 0 or block_index >= len(self.chain):
            raise IndexError("区块索引超出范围")
        
        # 如果没有提供私钥，则使用系统默认私钥
        if private_key is None:
            private_key = self.private_key
        
        # 获取要修改的区块和原始数据
        target_block = self.chain[block_index]
        original_data = target_block.data
        original_random = target_block.random_value
        
        # 创建原始区块字符串
        original_block_string = json.dumps({
            'index': target_block.index,
            'timestamp': target_block.timestamp,
            'data': original_data,
            'previous_hash': target_block.previous_hash
        }, sort_keys=True).encode()
        
        # 更新区块数据
        target_block.data = new_data
        
        # 创建新区块字符串
        new_block_string = json.dumps({
            'index': target_block.index,
            'timestamp': target_block.timestamp,
            'data': new_data,
            'previous_hash': target_block.previous_hash
        }, sort_keys=True).encode()
        
        # 找到碰撞，使哈希值保持不变
        try:
            new_random = self.chameleon_hash.find_collision(
                original_block_string, 
                new_block_string, 
                original_random,
                private_key
            )
            target_block.random_value = new_random
            
            # 重新计算哈希值，但应该与原始哈希相同
            chameleon = ChameleonHash()
            hash_value, _ = chameleon.hash(new_block_string, new_random)
            if hash_value.hex() != target_block.hash:
                # 如果哈希值不同，我们需要更新哈希值（在理想情况下不应该发生）
                target_block.hash = hash_value.hex()
                
                # 由于哈希值发生变化，需要更新所有后续区块的previous_hash
                self._update_subsequent_blocks(block_index)
            
            return True
        except PermissionError as e:
            # 权限错误
            print(f"权限错误: {e}")
            # 恢复原始数据
            target_block.data = original_data
            target_block.random_value = original_random
            # 重新抛出异常以便API处理
            raise e
        except Exception as e:
            # 恢复原始数据
            target_block.data = original_data
            target_block.random_value = original_random
            print(f"修改区块失败: {e}")
            return False
    
    def _update_subsequent_blocks(self, start_index):
        """
        更新从start_index开始的所有后续区块的previous_hash
        """
        for i in range(start_index + 1, len(self.chain)):
            self.chain[i].previous_hash = self.chain[i-1].hash
            # 重新计算当前区块的哈希值
            block_string = json.dumps({
                'index': self.chain[i].index,
                'timestamp': self.chain[i].timestamp,
                'data': self.chain[i].data,
                'previous_hash': self.chain[i].previous_hash
            }, sort_keys=True).encode()
            
            chameleon = ChameleonHash()
            hash_value, random_value = chameleon.hash(block_string)
            self.chain[i].hash = hash_value.hex()
            self.chain[i].random_value = random_value
    
    def to_dict(self):
        """将整个区块链转换为字典列表"""
        return [block.to_dict() for block in self.chain]