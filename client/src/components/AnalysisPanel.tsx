import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface AnalysisPanelProps {
  analysis: string;
  recommendedGear: string[];
  isStreaming: boolean;
}

export function AnalysisPanel({ analysis, recommendedGear, isStreaming }: AnalysisPanelProps) {
  if (!analysis && recommendedGear.length === 0) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">ルート分析</h3>
        <p className="text-gray-500 text-sm">
          ルートを生成すると AI による分析が表示されます
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">ルート分析</h3>
        {isStreaming && (
          <div className="flex items-center space-x-2">
            <div className="animate-pulse h-2 w-2 bg-blue-600 rounded-full"></div>
            <span className="text-xs text-gray-500">AI 分析中...</span>
          </div>
        )}
      </div>

      {/* LLM Analysis with Markdown rendering */}
      {analysis && (
        <div className="prose prose-sm max-w-none mb-6">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysis}</ReactMarkdown>
          {isStreaming && <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1"></span>}
        </div>
      )}

      {/* Recommended Gear */}
      {recommendedGear.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
          <h4 className="text-sm font-semibold text-blue-900 mb-3">推奨装備</h4>
          <ul className="space-y-2">
            {recommendedGear.map((gear, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                <span className="text-sm text-gray-700">{gear}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
