from src.app import app

if __name__ == "__main__":
    print("基于变色龙哈希的可修改区块链启动中...")
    print("请在浏览器中访问: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)