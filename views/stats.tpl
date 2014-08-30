% rebase('base.tpl', title='Stats')

Donation address is: {{current_address}}
<br>
Available funds are: {{symbol}}{{current_funds}}
<br>
Current payout is: {{symbol}}{{current_payout}}
<br>
Total pending payouts are: {{symbol}}{{next_payout_total}}
<br>
Total pay periods elapsed: {{total_pay_periods}}
<br>
Last payout was on {{last_payout_time}} for {{symbol}}{{last_payout_total}}
<br>
Next payout will be at {{next_payout_time}} for {{symbol}}{{next_payout_total}}
<br>
Current server time is {{current_time}}

