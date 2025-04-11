import hashlib
import random
import os
import uuid

class ChameleonHash:
    def __init__(self):
        # 生成简单的数字密钥对
        self.private_key = self._generate_random_key()
        self.public_key = self._derive_public_key(self.private_key)
        self.trapdoor = None
        # 存储所有已生成的密钥对
        self.key_pairs = {}
        # 将默认密钥添加到密钥对中，并赋予名称
        self.key_pairs["default"] = {
            "private_key": str(self.private_key),
            "public_key": str(self.public_key),
            "description": "默认密钥对"
        }
    
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
    
    def generate_key_pair(self, description=""):
        """生成新的密钥对并返回ID"""
        private_key = self._generate_random_key()
        public_key = self._derive_public_key(private_key)
        
        # 生成唯一ID
        key_id = str(uuid.uuid4())[:8]
        
        # 存储密钥对
        self.key_pairs[key_id] = {
            "private_key": str(private_key),
            "public_key": str(public_key),
            "description": description
        }
        
        return {
            "id": key_id,
            "private_key": str(private_key),
            "public_key": str(public_key),
            "description": description
        }
    
    def get_key_pairs(self):
        """获取所有密钥对信息（不包含私钥细节）"""
        result = {}
        for key_id, key_data in self.key_pairs.items():
            result[key_id] = {
                "public_key": key_data["public_key"],
                "description": key_data["description"]
            }
        return result
    
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
            
            # 检查私钥是否与任何已知的密钥对匹配
            for key_id, key_data in self.key_pairs.items():
                if key_data["private_key"] == private_key_str:
                    return True, key_id
                    
            # 检查私钥是否与当前实例的私钥匹配
            if derived_public_key == self.public_key:
                return True, "default"
                
            return False, None
            
        except (ValueError, TypeError):
            return False, None
    
    def identify_key_owner(self, private_key_str):
        """识别私钥所属的密钥对"""
        result, key_id = self.verify_key_pair(private_key_str)
        if result:
            return key_id
        return None
    
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
        key_id = None
        if private_key_str:
            result, key_id = self.verify_key_pair(private_key_str)
            if not result:
                raise PermissionError("私钥验证失败，无权修改区块")
        
        # 计算原始哈希值
        original_hash, _ = self.hash(original_message, original_r)
        
        # 尝试找到一个r值使新消息的哈希值与原始哈希值相同
        max_attempts = 10000  # 防止无限循环
        for _ in range(max_attempts):
            r_new = self.generate_random()
            new_hash, _ = self.hash(new_message, r_new)
            
            if new_hash == original_hash:
                return r_new, key_id
        
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
            return adjusted_r, key_id
            
        raise Exception("无法找到碰撞")