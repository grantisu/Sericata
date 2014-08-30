% rebase('base.tpl', title='')

Donation address is: {{current_address}}
<br>
Current payout is: {{symbol}}{{current_payout}}
<br>
<form action="/payout" method="post">
  Address: <input name="addr" type="text" />
  <input value="payout" type="Submit">
</form>

