console.log(window.innerWidth)

// Function makes a post request sending user form data to server. AJAX eliminates a response that refreshes page
let send = function()
{
	const query = document.querySelector('#query').value;
	const amount = document.querySelector('#amount').value;
	const f = document.getElementsByTagName("form")[0];
	let wrapper = document.querySelector('.form-wrapper');

  	const xhttp = new XMLHttpRequest();
  	xhttp.open("get", "/query" + "?" + "query=" + query + "&amount=" + amount);
	xhttp.setRequestHeader('Content-Type', 'application/json');

	xhttp.onreadystatechange = function()
	{
		
		if (xhttp.readyState == 4 && xhttp.status == 200)
		{	
			const data = JSON.parse(xhttp.responseText);
			if (data['response'] == true)
			{
				wrapper.innerHTML = data.html;
			}
		}
	}

	// let message = {query: query, amount: amount};
	// message = JSON.stringify(message);
	
	if (f.reportValidity())
	{	
		// console.log('message is' + message )
		xhttp.send(null)
	}
}
// Function sends get request to server with filename argument (with unique trailing number hidden in HTML) for server to retrieve, and return to client for download 
let download = function()
{	
	// Get key val from hidden HTML button to pass to server
	const hiddenVal = document.querySelector('.hidden_val').value;
	const param = "/" + hiddenVal;
	const xhttp = new XMLHttpRequest();
	xhttp.open("get", "/download" + param);

	xhttp.setRequestHeader('Content-Type', 'text/csv; charset=UTF-8');
	xhttp.onload = function()
	{
		if (xhttp.readyState == 4 && xhttp.status == 200) 
		{	
			// Figure out filename value, if possible.
			let disposition = xhttp.getResponseHeader('Content-Disposition')
	
			// Extract file name from response. Content Disposition: attachment; filename=python.csv
			const matches = /=([^=].+\.csv)/.exec(disposition)
			// Assign filename as the extracted xhttp.response as long as it is not null. if null or other error, assign generic 'file.csv' // Also removing trailing number for user
			let filename = (matches != null && matches[1] ? matches[1].substr(0, matches[1].length - 7) + ".csv" : 'file.csv')

			// Download
			const blob = new Blob([xhttp.response], { type: 'text/csv' })
			const link = document.createElement('a');
			link.href = window.URL.createObjectURL(blob);

			link.download = filename;

			document.body.appendChild(link);
			//LEARN! 
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

	let hiddenVal = document.querySelector('.hidden_val').value;

	if (hiddenVal)
	{	
		let xhttp = new XMLHttpRequest();
		xhttp.open("get", "clear/" + hiddenVal)
		xhttp.setRequestHeader('Content-Type', 'text/plain; charset=UTF-8')
		xhttp.onload = function()
		{	
			if (xhttp.readyState == 4 && xhttp.status == 200)
			{
				const reply = xhttp.responseText;

				if (reply == 'True')
				{
					window.location ="/";
				}
				else
				{	
					window.location ="/";
				}
			}
		}
		xhttp.send(null)
	}
	else
	{
		window.location = "/"
	}
}































