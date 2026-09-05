#!/usr/bin/env python3
"""Recalculate scenario CSVs from local CSV inputs; stdlib only, no network or secrets."""
from pathlib import Path
import csv
from collections import defaultdict

ROOT = Path(__file__).resolve().parent

def read(name):
    with (ROOT / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(name, rows):
    with (ROOT / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def money(x): return round(x, 2)

def calculate():
    skus = {r['sku']: {k: (v if k in ('sku','description') else float(v)) for k,v in r.items()} for r in read('financial-inputs-skus.csv')}
    settings = {r['parameter']: float(r['value']) for r in read('financial-assumptions.csv')}
    inputs = read('financial-scenarios.csv')
    economics = []
    for sku, r in skus.items():
        p = r['price_incl_tax']; vat = p * settings['vat_rate']/(1+settings['vat_rate'])
        refund = p * r['refund_rate']; fee = p * r['channel_fee_rate']
        warranty = r['manufacturing_cost'] * r['warranty_rate']
        variable = vat + refund + fee + r['fulfillment_cost'] + warranty + r['support_cost'] + r['cac'] + r['return_logistics_reserve']
        contribution = p - r['manufacturing_cost'] - variable
        economics.append({'sku':sku, 'price_incl_tax':p,'manufacturing_cost':r['manufacturing_cost'], 'vat_reserve_no_input_credit':money(vat), 'refund_reserve':money(refund), 'channel_fee':money(fee),'fulfillment':r['fulfillment_cost'],'warranty_reserve':money(warranty),'support_cost':r['support_cost'],'cac':r['cac'],'return_logistics_reserve':r['return_logistics_reserve'],'contribution_per_unit':money(contribution),'contribution_rate_on_gross_sales':round(contribution/p,4),'units_to_cover_monthly_fixed_opex':int(settings['monthly_fixed_opex']/contribution)+1 if contribution>0 else 'not_viable'})
        r['unit_variable_nonmanufacturing'] = variable
        r['unit_contribution'] = contribution
    write('financial-sku-economics.csv', economics)
    grouped = defaultdict(list)
    for r in inputs: grouped[r['scenario']].append(r)
    output=[]; summaries=[]
    for scenario, rows in grouped.items():
        rows.sort(key=lambda r:int(r['month']))
        cash=settings['starting_cash'];inventory={sku:0 for sku in skus};previous_receivable=0; cumulative_profit=-settings['upfront_nre'];cum_units=0
        first=rows[0]
        initial={sku:round(int(first[sku])*(1+settings['inventory_buffer_rate'])) for sku in skus}
        inv_payment=sum(initial[k]*skus[k]['manufacturing_cost'] for k in skus)
        cash-=settings['upfront_nre']+inv_payment;inventory=initial.copy()
        output.append({'scenario':scenario,'month':0,'units':0,'gross_sales':0,'cash_collected':0,'ending_receivable':0,'refund_reserve':0,'vat_reserve':0,'manufacturing_cogs':0,'other_variable_expense':0,'contribution':0,'fixed_opex':0,'nre_cash':settings['upfront_nre'],'operating_profit':-settings['upfront_nre'],'inventory_purchase_units':sum(initial.values()),'inventory_purchase_cash':money(inv_payment),'ending_inventory_units':sum(inventory.values()),'ending_inventory_value':money(inv_payment),'net_cash_flow':money(-settings['upfront_nre']-inv_payment),'ending_cash':money(cash)})
        min_cash=cash;first_negative='none_in_horizon'
        for i,r in enumerate(rows):
            month=int(r['month']);qty={sku:int(r[sku]) for sku in skus};units=sum(qty.values());cum_units+=units
            for sku in skus:
                if qty[sku]>inventory[sku]:raise ValueError(f'Insufficient inventory {scenario} month {month} {sku}')
                inventory[sku]-=qty[sku]
            gross=sum(qty[k]*skus[k]['price_incl_tax'] for k in skus)
            receivable=sum(qty[k]*skus[k]['price_incl_tax']*skus[k]['delayed_collection_share'] for k in skus)
            collected=gross-receivable+previous_receivable
            previous_receivable=receivable
            refund=sum(qty[k]*skus[k]['price_incl_tax']*skus[k]['refund_rate'] for k in skus)
            vat=gross*settings['vat_rate']/(1+settings['vat_rate'])
            manufacturing=sum(qty[k]*skus[k]['manufacturing_cost'] for k in skus)
            total_variable=sum(qty[k]*skus[k]['unit_variable_nonmanufacturing'] for k in skus)
            other=total_variable-refund-vat
            contribution=gross-manufacturing-total_variable
            fixed=settings['monthly_fixed_opex']*float(r['opex_multiplier'])
            profit=contribution-fixed;cumulative_profit+=profit
            next_qty={sku:int(rows[i+1][sku]) if i+1<len(rows) else round(qty[sku]*(1+settings['terminal_next_month_growth'])) for sku in skus}
            purchases={sku:max(0,round(next_qty[sku]*(1+settings['inventory_buffer_rate']))-inventory[sku]) for sku in skus}
            purchase_cash=sum(purchases[k]*skus[k]['manufacturing_cost'] for k in skus)
            for sku in skus:inventory[sku]+=purchases[sku]
            net_cash=collected-total_variable-fixed-purchase_cash;cash+=net_cash
            min_cash=min(min_cash,cash)
            if cash<0 and first_negative=='none_in_horizon':first_negative=month
            inventory_value=sum(inventory[k]*skus[k]['manufacturing_cost'] for k in skus)
            # Accounting identity: NRE expensed at month 0; gross receivables; reserves paid same month.
            expected=settings['starting_cash']+cumulative_profit-receivable-inventory_value
            if abs(cash-expected)>0.01:raise AssertionError((scenario,month,cash,expected))
            output.append({'scenario':scenario,'month':month,'units':units,'gross_sales':money(gross),'cash_collected':money(collected),'ending_receivable':money(receivable),'refund_reserve':money(refund),'vat_reserve':money(vat),'manufacturing_cogs':money(manufacturing),'other_variable_expense':money(other),'contribution':money(contribution),'fixed_opex':money(fixed),'nre_cash':0,'operating_profit':money(profit),'inventory_purchase_units':sum(purchases.values()),'inventory_purchase_cash':money(purchase_cash),'ending_inventory_units':sum(inventory.values()),'ending_inventory_value':money(inventory_value),'net_cash_flow':money(net_cash),'ending_cash':money(cash)})
        selected=[r for r in output if r['scenario']==scenario]
        summaries.append({'scenario':scenario,'total_units':cum_units,'total_gross_sales':money(sum(r['gross_sales'] for r in selected)),'total_contribution':money(sum(r['contribution'] for r in selected)),'cumulative_profit_after_nre':money(cumulative_profit),'ending_cash':money(cash),'minimum_cash':money(min_cash),'first_negative_cash_month':first_negative,'ending_receivable':money(previous_receivable),'ending_inventory_value':money(inventory_value)})
    write('financial-monthly.csv',output);write('financial-summary.csv',summaries)
    for r in summaries:print(r)

if __name__=='__main__':calculate()
