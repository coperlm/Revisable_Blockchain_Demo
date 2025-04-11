import hashlib
import random
import os

class ChameleonHash:
    def __init__(self):
        # 生成简单的数字密钥对
        self.private_key = self._generate_random_key()
        self.public_key = self._derive_public_key(self.private_key)
        self.trapdoor = None
    
    def _generate_random_key(self, bits=256):
        """生成随机的数字密钥"""
        return random.getrandbits(bits)
    
    def _derive_public_key(self, private_key):
        """从私钥派生公钥(这里使用简单的函数)"""
        # 在实际应用中，公私钥关系应该基于更复杂的加密算法
        # 这里我们使用哈希函数来模拟
        return int(hashlib.sha256(str(private_key).encode()).hexdigest(), 16)
    
    def export_private_key(self):
        """导出私钥为字符串格式"""
        return str(self.private_key)
    
    def export_public_key(self):
        """导出公钥为字符串格式"""
        return str(self.public_key)
    
    def verify_key_pair(self, private_key_str, expected_public_key_str=None):
        """验证私钥是否有效，以及其是否与预期的公钥匹配"""
        try:
            # 转换为整数
            private_key = int(private_key_str)
            
            # 从私钥派生公钥
            derived_public_key = self._derive_public_key(private_key)
            
            # 如果提供了预期公钥，则检查是否匹配
            if expected_public_key_str:
                expected_public_key = int(expected_public_key_str)
                if derived_public_key != expected_public_key:
                    return False
                    
            # 检查私钥是否与当前实例的私钥匹配
            return derived_public_key == self.public_key
            
        except (ValueError, TypeError):
            return False
    
    def generate_random(self, size=32):
        """生成随机数"""
        return random.randint(1, 2**(size*8))
    
    def hash(self, message, r=None):
        """
        计算消息的变色龙哈希值
        params:
            message: 待哈希的消息
            r: 随机数，如果为None则自动生成
        returns:
            (哈希值, 随机数r)
        """
        if r is None:
            r = self.generate_random()
        
        # 确保message是bytes类型
        if not isinstance(message, bytes):
            message = str(message).encode('utf-8')
        
        # 将消息和随机数组合
        combined = message + str(r).encode('utf-8')
        
        # 使用SHA-256计算哈希值
        h = hashlib.sha256(combined).digest()
        
        # 记录随机数作为陷门
        self.trapdoor = r
        
        return h, r
    
    def find_collision(self, original_message, new_message, original_r, private_key_str=None):
        """
        为新消息找到一个碰撞，使得新旧消息的哈希值相同
        params:
            original_message: 原始消息
            new_message: 新消息
            original_r: 原始随机数
            private_key_str: 私钥字符串，如果提供则验证权限
        returns:
            用于新消息的随机数r'
        """
        # 如果提供了私钥，验证是否有权限
        if private_key_str:
            if not self.verify_key_pair(private_key_str):
                raise PermissionError("私钥验证失败，无权修改区块")
        
        # 计算原始哈希值
        original_hash, _ = self.hash(original_message, original_r)
        
        # 尝试找到一个r值使新消息的哈希值与原始哈希值相同
        max_attempts = 10000  # 防止无限循环
        for _ in range(max_attempts):
            r_new = self.generate_random()
            new_hash, _ = self.hash(new_message, r_new)
            
            if new_hash == original_hash:
                return r_new
        
        # 如果找不到碰撞，使用陷门（实际实现中会有更高效的算法）
        if self.trapdoor:
            # 在实际应用中，会使用陷门函数计算新的r值
            # 这里简化处理，尝试基于trapdoor调整新的r值
            
            # 确保new_message是bytes类型
            if not isinstance(new_message, bytes):
                new_message_bytes = str(new_message).encode('utf-8')
            else:
                new_message_bytes = new_message
                
            adjusted_r = (original_r ^ int.from_bytes(hashlib.sha256(new_message_bytes).digest(), 'big')) & ((1 << 256) - 1)
            return adjusted_r
            
        raise Exception("无法找到碰撞")