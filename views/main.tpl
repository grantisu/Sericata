% rebase('base.tpl', title='')

<h1>Sericata Faucet</h1>

<div id="main_text">
Welcome, help yourself to some {{coin}}.
<p>
Current payout is: {{symbol}}{{current_payout}}
</div>
<form id="main_form" action="/payout" method="post">
<label for="addr">Address</label>
<input name="addr" id="addr" type="text">

{{!captcha_html}}

<input id="pay_button" value="Payout" type="Submit" {{current_payout and ' ' or 'disabled'}}>
</form>

