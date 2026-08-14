export function SceneLegend() {
  return (
    <div className="spatial-legend">
      <p className="spatial-legend-title">Legend</p>
      <ul className="space-y-2 text-xs text-white">
        <li className="spatial-legend-item"><span className="spatial-dot spatial-dot-safe" />Normal</li>
        <li className="spatial-legend-item"><span className="spatial-dot spatial-dot-warning" />Warning</li>
        <li className="spatial-legend-item"><span className="spatial-dot spatial-dot-critical" />Critical</li>
        <li className="spatial-legend-item"><span className="spatial-dot spatial-dot-occupants" />Occupants</li>
        <li className="spatial-legend-item"><span className="spatial-line spatial-line-safe" />Safe Route</li>
        <li className="spatial-legend-item"><span className="spatial-line spatial-line-blocked" />Blocked Route</li>
        <li className="spatial-legend-item"><span className="spatial-dot spatial-dot-resource" />Response Resource</li>
      </ul>
    </div>
  );
}