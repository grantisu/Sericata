% rebase('base.tpl', title='Stats')

<h1>Sericata Stats Page</h1>

<dl class='stats'>
<dt>Available funds</dt>
<dd>{{symbol}}{{current_funds}}</dd>
<dt>Current payout</dt>
<dd>{{symbol}}{{current_payout}}</dd>
<dt>Total pay periods</dt>
<dd>{{total_pay_periods}}</dd>
<dt>Total paid to date</dt>
<dd>{{symbol}}{{total_pay_amount}}</dd>
<dt>Last payout</dt>
<dd>{{symbol}}{{last_payout_total}} at <span id='last_time'>{{last_payout_time}}</span></dd>
<dt>Pending payouts</dt>
<dd>{{symbol}}{{next_payout_total}} <span id='next_time'>at {{next_payout_time}}</span></dd>
<span id='cur_time'>
<dt>Current server time</dt>
<dd>{{current_time}}</dd>
</span>
</dl>

<script>

var inc = 950; // msec
var interval;

var last_t  = new Date(1000*{{last_payout_time}});
var skew_ms = 1000*{{current_time}} - Date.now();
var next_ms = 1000*{{next_payout_time}} - skew_ms;

var last_n = document.getElementById('last_time');
var next_n = document.getElementById('next_time');
var cur_n = document.getElementById('cur_time');

last_n.innerHTML = last_t;
cur_n.innerHTML = '';

function update_times() {
	s = Math.floor(0.001*(next_ms - Date.now()) + 1);
	if (s >= 0) {
		next_n.innerHTML = 'in '+s+' sec';
	} else {
		window.clearInterval(interval);
		location.assign('?auto-stats');
	}
}

update_times();
interval = window.setInterval(update_times, inc);

</script>

