import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const AuthPage = () => {
  const { login, register, error: authError, isLoading } = useAuth();
  const [isLoginMode, setIsLoginMode] = useState(true);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isLoginMode) {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
    } catch (err) {
      
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4 relative overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-cyan-500/20 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="w-full max-w-md bg-gray-900/80 backdrop-blur-xl border border-gray-700 rounded-2xl shadow-2xl p-8 z-10">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 mb-2">
                    LUNG AI SYSTEM
                </h1>
                <p className="text-gray-400 text-sm">Hệ thống chẩn đoán ung thư phổi thông minh</p>
            </div>

            {authError && (
                <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-200 text-sm text-center">
                    {authError}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
                {!isLoginMode && (
                    <div>
                        <label className="block text-gray-400 text-xs font-bold uppercase mb-1">Họ và tên</label>
                        <input type="text" required className="w-full bg-gray-800/50 border border-gray-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-cyan-400 transition-colors" placeholder="Tên hiển thị..." value={name} onChange={(e) => setName(e.target.value)} />
                    </div>
                )}
                
                <div>
                    <label className="block text-gray-400 text-xs font-bold uppercase mb-1">Email</label>
                    <input type="email" required className="w-full bg-gray-800/50 border border-gray-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-cyan-400 transition-colors" placeholder="email@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>

                <div>
                    <label className="block text-gray-400 text-xs font-bold uppercase mb-1">Mật khẩu</label>
                    <input type="password" required className="w-full bg-gray-800/50 border border-gray-600 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-cyan-400 transition-colors" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
                </div>

                <button type="submit" disabled={isLoading} className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50">
                    {isLoading ? "Đang xử lý..." : (isLoginMode ? "ĐĂNG NHẬP" : "ĐĂNG KÝ")}
                </button>
            </form>

            <div className="mt-6 text-center">
                <p className="text-gray-500 text-sm">
                    <button onClick={() => { setIsLoginMode(!isLoginMode); }} className="text-cyan-400 hover:text-cyan-300 font-semibold underline decoration-transparent hover:decoration-cyan-300 transition-all">
                        {isLoginMode ? "Tạo tài khoản mới" : "Quay lại đăng nhập"}
                    </button>
                </p>
            </div>
        </div>
    </div>
  );
};

export default AuthPage;