% rebase('base.tpl', title='')

<h3>Sericata Faucet</h3>

Welcome, help yourself to some {{coin}}.
<p>
Current payout is: {{symbol}}{{current_payout}}
<br>
Donation address is: {{current_address}}
<br>
<form action="/payout" method="post">
Address: <input name="addr" type="text" />

{{!captcha_html}}

<input value="payout" type="Submit" {{current_payout and ' ' or 'disabled'}}>
</form>

