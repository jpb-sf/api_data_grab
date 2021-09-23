console.log(window.innerWidth)
// Function makes a get request sending user entered data to server.
let send = function()
{
	const query = document.querySelector('#query').value;
	const amount = document.querySelector('#amount').value;
	const f = document.getElementsByTagName("form")[0];
	let wrapper = document.querySelector('.form-wrapper');

	if (f.reportValidity())
	{	
		window.location = "/query?query=" + query + "&amount=" + amount
	}
}

// Function sends get request to server with filename argument (with unique trailing number hidden in HTML) for server to retrieve and return to client for download 
let download = function()
{	
	// Get key val from hidden HTML button to pass to server
	const hiddenVal = document.querySelector('.hidden_val').value;
	const arg = "/" + hiddenVal;
	const xhttp = new XMLHttpRequest();
	xhttp.open("get", "/download" + arg);

	xhttp.onload = function()
	{
		if (xhttp.readyState == 4 && xhttp.status == 200) 
		{	
			// Figure out filename value if possible.
			let disposition = xhttp.getResponseHeader('Content-Disposition')

			// Extract file name from response. Content Disposition: attachment; filename=python.csv
			const matches = /=([^=].+\.csv)/.exec(disposition)
			// Assign filename as the extracted xhttp.response as long as it's not null. If null or any other error, assign generic 'file.csv' // Also removing trailing number for user
			let filename = (matches != null ? matches[1].substr(0, matches[1].length - 7) + ".csv" : 'file.csv')
			console.log('matches is ')
			console.log(matches)
			console.log('matches[1] is ')
			console.log(matches[1])
			// Download
			const blob = new Blob([xhttp.response], { type: 'text/csv' })
			const link = document.createElement('a');
			link.href = window.URL.createObjectURL(blob);

			link.download = filename;

			document.body.appendChild(link);
			link.click();

			document.body.removeChild(link);
		}
	}
	xhttp.send(null)
}

// Resets form values
let reset = function()
{
	let values = document.querySelectorAll(input);
	values.forEach(function (item) 
		{
			item.value="";
		}) 
}

// Function returns user to home page. If there is a hidden value, the server will be notified of the file to clear
let home = function() {

	let hiddenVal = document.querySelector('.hidden_val');
	if (hiddenVal)
	{
		
		let xhttp = new XMLHttpRequest();
		xhttp.open("get", "clear/" + hiddenVal.value)
		xhttp.setRequestHeader('Content-Type', 'text/plain; charset=UTF-8')
		xhttp.onload = function()
		{	
			if (xhttp.readyState == 4 && xhttp.status == 200)
			{
				window.location.href = "/"
			}
		}
		xhttp.send(null)
	}
	else
	{
		window.location.href = "/"
	}
}































