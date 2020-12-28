//@version=4
//WRITTEN IN PINE

strategy(title = "SQZMOM STRAT", overlay=false, initial_capital = 1, commission_type=strategy.commission.percent, commission_value=0, default_qty_type = strategy.percent_of_equity, default_qty_value = 100)

// --- GENERAL INPUTS ---
FromMonth = input(defval = 4, title = "From Month", minval = 1, maxval = 12)
FromYear  = input(defval = 2020, title = "From Year", minval = 2012)
ToMonth   = input(defval = 1, title = "To Month", minval = 1, maxval = 12)
ToYear    = input(defval = 9999, title = "To Year", minval = 2017)
FromDay   = 1
ToDay     = 1
start     = timestamp(FromYear, FromMonth, FromDay, 00, 00)  // backtest start window
finish    = timestamp(ToYear, ToMonth, ToDay, 23, 59)        // backtest finish window
window()  => time >= start and time <= finish ? true : false // create function "within window of time"

get_round(value, precision) => round(value * (pow(10, precision))) / pow(10, precision)
trade_leverage = input(1, title = "Trade - Leverage", step = 0.25)
trade_risk     = input(100, title = "Trade - Risk Percent", type = input.float, step = 0.1, minval = 0.1, maxval = 100)
tradeType   = input("LONG", title="What trades should be taken : ", options=["LONG", "SHORT", "BOTH"])

// --- SQZMOM CODE

length = input(21, title="BB Length")
mult = input(2.0,title="BB MultFactor")
lengthKC=input(20, title="KC Length")
multKC = input(1.5, title="KC MultFactor")

useTrueRange = input(true, title="Use TrueRange (KC)", type=input.bool)

// Calculate BB
source = close
basis = sma(source, length)
dev = multKC * stdev(source, length)
upperBB = basis + dev
lowerBB = basis - dev

// Calculate KC
ma = sma(source, lengthKC)
range = useTrueRange ? tr : (high - low)
rangema = sma(range, lengthKC)
upperKC = ma + rangema * multKC
lowerKC = ma - rangema * multKC

sqzOn  = (lowerBB > lowerKC) and (upperBB < upperKC)
sqzOff = (lowerBB < lowerKC) and (upperBB > upperKC)
noSqz  = (sqzOn == false) and (sqzOff == false)

val = linreg(source  -  avg(avg(highest(high, lengthKC), lowest(low, lengthKC)),sma(close,lengthKC)), lengthKC,0)

bcolor = color.gray
if (val > 0 and val > nz(val[1]))
    bcolor := color.green
if (val < 0 and val < nz(val[1]))
    bcolor := color.red

scolor = noSqz ? color.blue : sqzOn ? color.black : color.gray
plot(val, color=bcolor, style=plot.style_histogram, linewidth=4)
plot(0, color=scolor, style=plot.style_cross, linewidth=2)

// --- VWMA CODE ---
useVWMA        = input(false, title = "Use VWMA to selectively long/short?", type = input.bool)
lengthVWMA=input(42, title = "VWMA Length", step = 1, minval = 1)
useCV=input(false, type=input.bool, title="Use Cumulative Volume for VWMA?")
nbfs = useCV ? cum(volume) : sum(volume, lengthVWMA)
medianSrc=close

calc_evwma(price, lengthVWMA, nb_floating_shares) => data = (nz(close[1]) * (nb_floating_shares - volume)/nb_floating_shares) + (volume*price/nb_floating_shares)

m=calc_evwma(medianSrc, lengthVWMA, nbfs)


// ---STRATEGY---
if ((tradeType == "LONG" or tradeType == "BOTH") and (m>0 or useVWMA == false))
    longCondition = (val > 0 and noSqz == 0 and sqzOn == 0 and sqzOn[1] == 1)
    if (longCondition)
        contracts = get_round((strategy.equity * trade_leverage / close) * (trade_risk / 100), 4)
        strategy.entry("LONG", strategy.long, qty = contracts, when = window())

if((tradeType == "SHORT" or tradeType == "BOTH") and (m<0 or useVWMA == false))
    shortCondition = (val < 0 and noSqz == 0 and sqzOn == 0 and sqzOn[1] == 1)
    if (shortCondition)
        contracts = get_round((strategy.equity * trade_leverage / close) * (trade_risk / 100), 4)
        strategy.entry("SHORT", strategy.short, qty = contracts, when = window())

if (bcolor == color.gray)
    strategy.close("LONG")
    strategy.close("SHORT")
