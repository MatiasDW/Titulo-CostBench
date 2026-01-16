import React from 'react';

const RankingTable = ({ items, currency }) => {
    return (
        <div className="table-responsive">
            <table className="table table-dark table-hover align-middle mb-0">
                <thead>
                    <tr style={{ borderBottom: '2px solid #30363d' }}>
                        <th scope="col" className="text-secondary fw-bold" style={{ width: '8%' }}>Rank</th>
                        <th scope="col" className="text-secondary fw-bold">Institution</th>
                        <th scope="col" className="text-secondary fw-bold">Product</th>
                        <th scope="col" className="text-end text-secondary fw-bold">Annual Total Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item, index) => (
                        <tr key={`${item.institution}-${item.product}`}>
                            <td className="text-muted font-monospace">{index + 1}</td>
                            <td className="fw-semibold text-light">{item.institution}</td>
                            <td className="text-secondary">{item.product}</td>
                            <td className="text-end font-monospace text-light">
                                {currency === 'UF'
                                    ? `${item.cost.toLocaleString('es-CL', { minimumFractionDigits: 2 })} UF`
                                    : currency === 'USD'
                                        ? `${item.cost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`
                                        : `$${item.cost.toLocaleString('es-CL')} CLP`
                                }
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default RankingTable;
