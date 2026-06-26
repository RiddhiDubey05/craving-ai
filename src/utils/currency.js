// Free, no-key currency helper. Maps country -> currency symbol + a rough
// price multiplier so estimated prices feel realistic per region.
// (These are estimates for display purposes, not live exchange rates.)

export const CURRENCY_BY_COUNTRY = {
  India: { symbol: '₹', code: 'INR', multiplier: 1 },
  'United States': { symbol: '$', code: 'USD', multiplier: 0.18 },
  'United Kingdom': { symbol: '£', code: 'GBP', multiplier: 0.14 },
  'United Arab Emirates': { symbol: 'AED ', code: 'AED', multiplier: 0.66 },
  Australia: { symbol: 'A$', code: 'AUD', multiplier: 0.27 },
  Canada: { symbol: 'C$', code: 'CAD', multiplier: 0.25 }
};

export const DEFAULT_CURRENCY = { symbol: '₹', code: 'INR', multiplier: 1 };

export const getCurrencyForCountry = (country) => {
  return CURRENCY_BY_COUNTRY[country] || DEFAULT_CURRENCY;
};

export const formatPrice = (baseInrAmount, country) => {
  const currency = getCurrencyForCountry(country);
  const converted = Math.round(baseInrAmount * currency.multiplier);
  return `${currency.symbol}${converted}`;
};
