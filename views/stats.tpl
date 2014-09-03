% rebase('base.tpl', title='Stats')

<h3>Sericata Stats Page</h3>

Available funds are: {{symbol}}{{current_funds}}
<br>
Current payout is: {{symbol}}{{current_payout}}
<br>
Total pending payouts are: {{symbol}}{{next_payout_total}}
<br>
Total pay periods elapsed: {{total_pay_periods}}
<br>
Last payout was at <span id='last_time'>{{last_payout_time}}</span> for {{symbol}}{{last_payout_total}}
<br>
Next payout will be <span id='next_time'>at {{next_payout_time}}</span> for {{symbol}}{{next_payout_total}}
<br>
<span id='cur_time'>Current server time is {{current_time}}</span>

<script>

var inc = 200; // msec
var interval;

var last_t = new Date(1000*{{last_payout_time}});
var next_t = {{next_payout_time}};
var cur_t = {{current_time}};

var last_n = document.getElementById('last_time');
var next_n = document.getElementById('next_time');
var cur_n = document.getElementById('cur_time');

last_n.innerHTML = last_t;
cur_n.innerHTML = '';

function update_times() {
	s = Math.floor(1 + next_t - cur_t);
	if (s >= 0) {
		next_n.innerHTML = 'in '+s+' sec';
	} else {
		window.clearInterval(interval);
		location.reload(true)
	}
	cur_t += 0.001*inc;
}

update_times();
interval = window.setInterval(update_times, inc);

</script>

