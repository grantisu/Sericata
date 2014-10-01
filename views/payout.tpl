% rebase('base.tpl', title='Payout')

<h1>Success!</h1>

Scheduled payment of {{symbol}}{{amount}} to {{address}}

<div id="redir"></div>

<script>

var rtime = 10000; // msec
var inc   =   950; // msec
var interval;


redir_node = document.getElementById('redir');
redir_node.innerHTML = '<p>Redirecting to stats page in <span id="countdown"></span> seconds';

var deadline = rtime + Date.now();
var count_node = document.getElementById('countdown');

function update_time() {
	s = Math.floor(0.001*(deadline - Date.now()));
	if (s >= 0) {
		count_node.innerHTML = s;
	} else {
		window.clearInterval(interval);
		location.assign('/stats?auto-payout');
	}
}

update_time();
interval = window.setInterval(update_time, inc);

</script>

