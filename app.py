import React, { useState } from 'react';
import { FarmData, ViewMode } from './types';
import { INITIAL_DATA } from './constants';
import { InputGroup } from './components/InputGroup';
import { ResultRow } from './components/ResultRow';
import { calculateResults, formatCurrency, formatNumber } from './utils/calculations';
import { 
  Calculator, 
  LayoutDashboard, 
  Sprout, 
  Users, 
  Coins, 
  ShoppingCart, 
  FileText,
  TrendingUp
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const App: React.FC = () => {
  const [data, setData] = useState<FarmData>(INITIAL_DATA);
  const [viewMode, setViewMode] = useState<ViewMode>('resultados');

  const updateData = (key: keyof FarmData, val: number) => {
    setData(prev => ({ ...prev, [key]: val }));
  };

  const results = calculateResults(data);

  // Data for chart
  const chartData = [
    { name: 'Receita Líq', value: results.fatLiq, color: '#16a34a' },
    { name: 'Desembolso', value: results.desembolsoOp, color: '#dc2626' },
    { name: 'Lucro Líq', value: results.lucro, color: results.lucro >= 0 ? '#15803d' : '#991b1b' },
  ];

  const renderVariables = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
      {/* 1. Rebanho e Produção */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
          <Sprout className="w-5 h-5 text-green-600" />
          <h3 className="font-semibold text-gray-800">1. Rebanho e Produção</h3>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InputGroup label="Vacas Lactação" value={data.qtdVacasLac} onChange={v => updateData('qtdVacasLac', v)} step={1} />
          <InputGroup label="Litros/Vaca" value={data.litrosVaca} onChange={v => updateData('litrosVaca', v)} />
          <InputGroup label="Preço Leite" value={data.precoLeite} onChange={v => updateData('precoLeite', v)} prefix="R$" />
          <InputGroup label="Bezerras (Leite)" value={data.qtdBezAmam} onChange={v => updateData('qtdBezAmam', v)} step={1} />
          <InputGroup label="Leite/Bezerra (L)" value={data.leiteBezDia} onChange={v => updateData('leiteBezDia', v)} />
          <InputGroup label="Vacas Pré-Parto" value={data.qtdPreParto} onChange={v => updateData('qtdPreParto', v)} step={1} />
          <InputGroup label="Qtd. Recria Total" value={data.qtdRecria} onChange={v => updateData('qtdRecria', v)} step={1} />
        </div>
      </div>

      {/* 2. Custos Nutrição */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
          <ShoppingCart className="w-5 h-5 text-orange-600" />
          <h3 className="font-semibold text-gray-800">2. Custos Nutrição</h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
             <div>
                <h4 className="text-xs font-bold text-gray-400 uppercase mb-2">Preços (R$)</h4>
                <InputGroup label="Preço Conc. Lac" value={data.pConcLac} onChange={v => updateData('pConcLac', v)} prefix="R$" />
                <InputGroup label="Preço Conc. Pre" value={data.pConcPre} onChange={v => updateData('pConcPre', v)} prefix="R$" />
                <InputGroup label="Preço Polpa" value={data.pPolpa} onChange={v => updateData('pPolpa', v)} prefix="R$" />
             </div>
             <div>
                <h4 className="text-xs font-bold text-gray-400 uppercase mb-2">Consumo (Kg)</h4>
                <InputGroup label="Consumo Lac (Kg)" value={data.kgConcLac} onChange={v => updateData('kgConcLac', v)} suffix="kg" />
                <InputGroup label="Consumo Pre (Kg)" value={data.kgConcPre} onChange={v => updateData('kgConcPre', v)} suffix="kg" />
                <InputGroup label="Consumo Polpa" value={data.kgPolpa} onChange={v => updateData('kgPolpa', v)} suffix="kg" />
             </div>
          </div>
          <div className="border-t pt-4">
            <InputGroup label="Custo Recria/Sal (Fixo)" value={data.custoRecriaFixo} onChange={v => updateData('custoRecriaFixo', v)} prefix="R$" />
            <div className="grid grid-cols-2 gap-4 mt-2 bg-gray-50 p-3 rounded">
               <InputGroup label="Ref. Silagem Lac" value={data.kgSilLac} onChange={v => updateData('kgSilLac', v)} suffix="kg" />
               <InputGroup label="Ref. Silagem Pre" value={data.kgSilPre} onChange={v => updateData('kgSilPre', v)} suffix="kg" />
            </div>
          </div>
        </div>
      </div>

      {/* 3. Pessoal */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
          <Users className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-800">3. Pessoal (Base Encargos)</h3>
        </div>
        <div className="p-4">
          <div className="bg-blue-50 p-2 text-xs text-blue-800 rounded mb-4">
             ℹ️ Base de cálculo encargos: 21,2%
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InputGroup label="Salário 1 (Ord)" value={data.salOrd1} onChange={v => updateData('salOrd1', v)} prefix="R$" />
            <InputGroup label="Bonificação 1" value={data.bonifOrd1} onChange={v => updateData('bonifOrd1', v)} prefix="R$" />
            <InputGroup label="Salário 2 (Trat)" value={data.salTrat1} onChange={v => updateData('salTrat1', v)} prefix="R$" />
            <InputGroup label="Bonificação 2" value={data.bonifTrat1} onChange={v => updateData('bonifTrat1', v)} prefix="R$" />
            <InputGroup label="Outros (S/ Encargo)" value={data.salOrd2} onChange={v => updateData('salOrd2', v)} prefix="R$" />
          </div>
        </div>
      </div>

       {/* 4. Outros Custos */}
       <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-800">4. Outros Custos & Provisões</h3>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-6">
           <div>
             <h4 className="text-sm font-bold text-gray-700 mb-3 border-b pb-1">Custos Fixos</h4>
             <InputGroup label="GEA" value={data.custoGEA} onChange={v => updateData('custoGEA', v)} prefix="R$" />
             <InputGroup label="Lojas Agropec" value={data.custoLojas} onChange={v => updateData('custoLojas', v)} prefix="R$" />
             <InputGroup label="Alta Genetics" value={data.custoAlta} onChange={v => updateData('custoAlta', v)} prefix="R$" />
             <InputGroup label="Outros Fixos" value={data.custoOutros} onChange={v => updateData('custoOutros', v)} prefix="R$" />
           </div>
           <div>
             <h4 className="text-sm font-bold text-gray-700 mb-3 border-b pb-1">Provisões</h4>
             <InputGroup label="Silagem (Reposição)" value={data.provSilagem} onChange={v => updateData('provSilagem', v)} prefix="R$" />
             <InputGroup label="Financiamentos" value={data.provFinanc} onChange={v => updateData('provFinanc', v)} prefix="R$" />
             <InputGroup label="Adubação" value={data.provAdubo} onChange={v => updateData('provAdubo', v)} prefix="R$" />
             <InputGroup label="Depreciação" value={data.deprecTotal} onChange={v => updateData('deprecTotal', v)} prefix="R$" />
           </div>
        </div>
      </div>
    </div>
  );

  const renderResults = () => (
    <div className="space-y-6 pb-20">
      
      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-between">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-sm text-gray-500 font-medium uppercase">Lucro Líquido</p>
                    <h2 className={`text-2xl font-bold mt-1 ${results.lucro >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(results.lucro)}
                    </h2>
                </div>
                <div className={`p-2 rounded-lg ${results.lucro >= 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                    <TrendingUp className="w-6 h-6" />
                </div>
            </div>
            <div className="w-full h-24">
                 <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                        <Tooltip 
                            formatter={(value: number) => formatCurrency(value)}
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
             <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-sm text-gray-500 font-medium uppercase">EBITDA</p>
                    <h2 className="text-2xl font-bold mt-1 text-blue-600">{formatCurrency(results.ebitda)}</h2>
                </div>
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                    <Coins className="w-6 h-6" />
                </div>
            </div>
            <div className="space-y-3 mt-6">
                <ResultRow label="Custo por Litro" value={formatCurrency(results.custoLitro)} bold />
                <ResultRow label="Endividamento" value={`${formatNumber(results.endividamento, 1)}%`} />
            </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-sm text-gray-500 font-medium uppercase">Produção Mensal</p>
                    <h2 className="text-2xl font-bold mt-1 text-gray-800">{formatNumber(results.prodEntregueMes)} L</h2>
                </div>
                <div className="p-2 rounded-lg bg-gray-100 text-gray-600">
                    <LayoutDashboard className="w-6 h-6" />
                </div>
            </div>
            <div className="space-y-3 mt-6">
                 <ResultRow label="Vacas Lactação" value={formatNumber(results.vacasLac)} />
                 <ResultRow label="Litros/Vaca" value={formatNumber(data.litrosVaca, 1)} />
                 <ResultRow label="Prod. Entregue (x2)" value={`${formatNumber(results.prodEntregueX2)} L`} />
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Desembolso Mensal */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-red-50 px-4 py-3 border-b border-red-100 flex items-center justify-between">
            <h3 className="font-bold text-red-900 flex items-center gap-2">
                <ShoppingCart className="w-4 h-4" /> Desembolso Mensal
            </h3>
            <span className="font-bold text-red-700">{formatCurrency(results.desembolsoOp)}</span>
          </div>
          <div className="p-4 space-y-1">
             <ResultRow label="Concentrado Total" value={formatCurrency(results.totalConcentrado)} />
             <ResultRow label="Polpa + Caroço" value={formatCurrency(results.cPolpa)} />
             <ResultRow label="GEA" value={formatCurrency(data.custoGEA)} />
             <ResultRow label="Lojas Agropec." value={formatCurrency(data.custoLojas)} />
             <ResultRow label="Alta Genetics" value={formatCurrency(data.custoAlta)} />
             <ResultRow label="Pessoal (+ Encargos)" value={formatCurrency(results.custoPessoalTotal)} />
             <ResultRow label="Outros" value={formatCurrency(data.custoOutros)} />
             <div className="border-t border-gray-200 mt-2 pt-2 flex justify-between font-bold text-gray-900">
                 <span>TOTAL OPERACIONAL</span>
                 <span>{formatCurrency(results.desembolsoOp)}</span>
             </div>
          </div>
        </div>

        {/* Fluxo de Caixa */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-green-50 px-4 py-3 border-b border-green-100 flex items-center justify-between">
            <h3 className="font-bold text-green-900 flex items-center gap-2">
                <Coins className="w-4 h-4" /> Fluxo de Caixa
            </h3>
            <span className="font-bold text-green-700">{formatCurrency(results.fatLiq)}</span>
          </div>
          <div className="p-4 space-y-1">
             <ResultRow label="Receita Líquida" value={formatCurrency(results.fatLiq)} bold />
             <ResultRow label="(+) Saldo Operacional" value={formatCurrency(results.saldoOp)} highlight />
             
             <div className="bg-red-50 p-2 rounded-md mt-2 border border-red-100">
                <ResultRow label="(-) Total Provisionar" value={formatCurrency(results.totalProv)} colorClass="text-red-700" bold />
             </div>
             
             <div className="pl-2 space-y-1 mt-1">
                <ResultRow label="• Silagem" value={formatCurrency(data.provSilagem)} sub colorClass="text-gray-600" />
                <ResultRow label="• Financ." value={formatCurrency(data.provFinanc)} sub colorClass="text-gray-600" />
                <ResultRow label="• Adubação" value={formatCurrency(data.provAdubo)} sub colorClass="text-gray-600" />
                <ResultRow label="• Encargos (21,2%)" value={formatCurrency(results.encargos)} sub colorClass="text-gray-600" />
             </div>

             <div className={`mt-4 p-3 rounded-lg text-center border ${results.lucro >= 0 ? 'bg-green-100 border-green-200 text-green-800' : 'bg-red-100 border-red-200 text-red-800'}`}>
                 <span className="block text-xs uppercase font-bold tracking-wider mb-1">Resultado Final (Lucro)</span>
                 <span className="text-xl font-black">{formatCurrency(results.lucro)}</span>
             </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
             <h3 className="font-bold text-gray-800">Pontos de Equilíbrio (Break-Even)</h3>
          </div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
             <div className="p-3 bg-gray-50 rounded border border-gray-200">
                <span className="text-xs text-gray-500 uppercase">P.E. (C.O.E)</span>
                <p className="text-lg font-bold text-gray-800">{formatNumber(results.peCoe)} L</p>
             </div>
             <div className="p-3 bg-gray-50 rounded border border-gray-200">
                <span className="text-xs text-gray-500 uppercase">P.E. (C.O.T)</span>
                <p className="text-lg font-bold text-gray-800">{formatNumber(results.peCot)} L</p>
             </div>
             <div className="p-3 bg-gray-50 rounded border border-gray-200">
                <span className="text-xs text-gray-500 uppercase">P.E. (C.T)</span>
                <p className="text-lg font-bold text-gray-800">{formatNumber(results.peCt)} L</p>
             </div>
          </div>
      </div>

    </div>
  );

  return (
    <div className="min-h-screen flex flex-col md:flex-row font-sans text-gray-900">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-white border-r border-gray-200 flex flex-col md:fixed md:h-full z-10">
        <div className="p-6 border-b border-gray-100">
           <div className="flex items-center gap-2 text-green-700 mb-1">
             <Sprout className="w-6 h-6" />
             <span className="font-bold text-lg tracking-tight">Sítio Cangerana</span>
           </div>
           <p className="text-xs text-gray-400">Sistema de Gestão</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
            <button
                onClick={() => setViewMode('resultados')}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                viewMode === 'resultados'
                    ? 'bg-green-50 text-green-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
            >
                <LayoutDashboard className="w-5 h-5" />
                Painel de Resultados
            </button>
            <button
                onClick={() => setViewMode('variaveis')}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                viewMode === 'variaveis'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
            >
                <Calculator className="w-5 h-5" />
                Editar Variáveis
            </button>
        </nav>

        <div className="p-4 border-t border-gray-100">
            <div className="bg-gray-50 rounded p-3 text-xs text-gray-500">
                <p>Cenário Atual:</p>
                <strong className="text-gray-700">Padrão (Simulado)</strong>
            </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 md:ml-64 p-4 md:p-8 overflow-y-auto">
        <header className="mb-8 flex justify-between items-center">
             <div>
                <h1 className="text-2xl font-bold text-gray-900">
                    {viewMode === 'variaveis' ? 'Editar Variáveis' : 'Demonstrativo de Resultado'}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                    {viewMode === 'variaveis' 
                    ? 'Ajuste os parâmetros de produção e custos para recalcular o cenário.' 
                    : 'Visão consolidada dos indicadores financeiros e operacionais.'}
                </p>
             </div>
             {viewMode === 'variaveis' && (
                 <button 
                    onClick={() => setViewMode('resultados')}
                    className="hidden sm:flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm"
                 >
                    Ver Resultados <TrendingUp className="w-4 h-4" />
                 </button>
             )}
        </header>
        
        <div className="max-w-6xl mx-auto">
           {viewMode === 'variaveis' ? renderVariables() : renderResults()}
        </div>
      </main>
    </div>
  );
};

export default App;
