import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Cell,
  } from "recharts";
  
  const COLORS = {
    automate: "#22c55e",
    augment: "#f59e0b",
    "create-new": "#3b82f6",
    eliminate: "#ef4444",
  };
  
  const LABELS = {
    automate: "Automate",
    augment: "Augment",
    "create-new": "Create New",
    eliminate: "Eliminate",
  };
  
  export default function ImpactChart({ summary }) {
    const data = [
      "automate",
      "augment",
      "create-new",
      "eliminate",
    ].map((key) => ({
      impact: LABELS[key],
      value: summary?.[key] ?? 0,
      color: COLORS[key],
    }));
  
    return (
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="mb-4 font-display text-sm font-semibold text-text-primary">
          AI Impact Distribution
        </h3>
  
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2f3545" />
            <XAxis dataKey="impact" tick={{ fill: "#9ca3af", fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fill: "#9ca3af" }} />
            <Tooltip />
  
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.color}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }