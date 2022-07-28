var a0 = document.getElementById( 'a0' );
var t0 = document.getElementById( 't0' );

a0.addEventListener( 'click', e => {
	let v = window.prompt( 'Enter certificate CN', '' );
	if ( v ) {
		fetch( '/cert.cgi/' + v, { method: 'POST' } )
		.then( r => r.json() )
		.then( r => {
			location.reload();
		} );
	}
	e.preventDefault();
	return false;
} );

function formatDate( timestamp ) {
	let val = new Date( timestamp * 1000 );
	return [ new String( val.getFullYear() ), new String( val.getMonth() + 101 ).substring( 1 ), new String( val.getDate() + 100 ).substring( 1 ) ].join( '-' );
}

Promise.all( [ fetch( '/cert.cgi/' ), fetch( '/user.cgi/' ) ] )
.then( r => Promise.all( [ r[0].json(), r[1].json() ] ) )
.then( r => {
	let el;
	for ( let i in r[0] ) {
		let row = t0.tBodies[0].insertRow();
		let now = Math.floor( Date.now() / 1000 );

		for ( let j = 0; j < 8; j++ ) row.insertCell();

		//row.dataset.name = i;
		row.cells[0].innerHTML = i;
		
		el = document.createElement('a');
		el.href = '/dl.cgi/' + i;
		el.download = i + '.ovpn';
		el.innerHTML = 'Download';
		row.cells[1].appendChild( el );

		el = document.createElement('a');
		el.href = '/ui.cgi/edit/' + i;
		el.innerHTML = 'Manage';
		row.cells[2].appendChild( el );

		row.cells[7].innerHTML = formatDate( r[0][i].enddate );
		if ( r[0][i].enddate - now < 0 ) {
			row.className = 'mask';
		} else if ( r[0][i].enddate - now < 7 * 86400 ) {
			row.className = 'warn';
		}

		if ( r[1][i] ) {
			let user = r[1][i];
			let time = now - user.time;
			let unit = 'second';
			let tx = Math.round( Math.log( user.tx / 1000000 + 1 ) * 10 );
			let rx = Math.round( Math.log( user.rx / 1000000 + 1 ) * 10 );

			row.cells[3].innerHTML = user.ip;

			[[60,'minute'], [60,'hour'], [24,'day']].every( t => {
				if ( time > t[0] ) {
					time = Math.round( time / t[0] );
					unit = t[1];
					return true;
				}
			} );
			if ( time !== 1 ) unit += 's';
			row.cells[4].innerHTML = time + ' ' + unit;

			unit = 'b';
			['K', 'M', 'G'].every( t => {
				if ( ( user.tx > 1024 ) && ( user.rx > 1024 ) ) {
					user.tx = Math.round( user.tx / 1024 );
					user.rx = Math.round( user.rx / 1024 );
					unit = t;
					return true;
				}
			});
			row.cells[5].style = 'background-image: url(/ui.cgi/status?tx=' + tx + '&rx=' + rx + ');';
			row.cells[5].title = 'TX: ' + user.tx + unit + ' / RX: ' + user.rx + unit;
		}

	}
} );

