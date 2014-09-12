% rebase('base.tpl', title='')

<h1>Sericata Faucet</h1>

Welcome, help yourself to some {{coin}}.
<p>
Current payout is: {{symbol}}{{current_payout}}
<br>
<form action="/payout" method="post">
Address: <input name="addr" type="text" />

{{!captcha_html}}

<input value="payout" type="Submit" {{current_payout and ' ' or 'disabled'}}>
</form>

