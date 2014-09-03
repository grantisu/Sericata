<html>
<head>
  <title>{{ "Sericata" + (title and " - "+title or "") }}</title>
  <link rel="stylesheet" type="text/css" href="./style.css">
</head>
<body>
{{!base}}

<div>
<ul>
<li><a href="./">Main</a></li>
<li><a href="./stats">Stats</a></li>
</ul>
Donate: <a href="./donate.png">{{current_address}}</a>
</body>
</html>
