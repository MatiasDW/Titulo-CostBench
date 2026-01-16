import React from 'react';

const Filters = ({ limit, onLimitChange, currency, onCurrencyChange, onUpdate }) => {
    return (
        <div className="card-custom p-4 mb-4">
            <div className="row g-3">
                <div className="col-md-6">
                    <label className="form-label text-secondary small">Items to Show</label>
                    <select
                        className="form-select"
                        value={limit}
                        onChange={(e) => onLimitChange(parseInt(e.target.value))}
                    >
                        <option value="5">Top 5 Cheapest</option>
                        <option value="10">Top 10 Cheapest</option>
                        <option value="20">Top 20 Cheapest</option>
                        <option value="50">Top 50 Cheapest</option>
                    </select>
                </div>
                <div className="col-md-6">
                    <label className="form-label text-secondary small">Currency Denomination</label>
                    <select
                        className="form-select"
                        value={currency}
                        onChange={(e) => onCurrencyChange(e.target.value)}
                    >
                        <option value="CLP">CLP (Chilean Peso)</option>
                        <option value="UF">UF (Unidad de Fomento)</option>
                        <option value="USD">USD (US Dollar)</option>
                        <option value="BTC">BTC (Bitcoin)</option>
                        <option value="ETH">ETH (Ether)</option>
                        <option value="XRP">XRP (Ripple)</option>
                    </select>
                </div>
            </div>
            <div className="row mt-3">
                <div className="col-12">
                    <button className="btn btn-success w-100 fw-bold" onClick={onUpdate}>
                        Update Ranking
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Filters;
