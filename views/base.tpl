<html>
<head>
  <title>{{ "Sericata" + (title and " - "+title or "") }}</title>
  <link rel="stylesheet" type="text/css" href="./style.css">
  <meta name="viewport" content="width=device-width">
</head>
<body>
{{!base}}

<div id="footer">
<ul id="menu">
<li><a href="./">Main</a></li>
<li><a href="./stats">Stats</a></li>
</ul>
<span id="donate">Donate: <a href="./donate.png">{{current_address}}</a></span>
<div id="attrib">
&copy; <a href="http://www.gmathews.com">Grant Mathews</a> - <a href="https://github.com/grantisu/Sericata">source code</a>
</div>

</body>
</html>
