var a0 = document.getElementById( 'a0' );
var a1 = document.getElementById( 'a1' );
var t0 = document.getElementById( 't0' );
var c0 = null;
var now = Math.round( Date.now() / 1000 );

function formatDate( timestamp ) {
	let val = new Date( timestamp * 1000 );
	return [ new String( val.getFullYear() ), new String( val.getMonth() + 101 ).substring( 1 ), new String( val.getDate() + 100 ).substring( 1 ) ].join( '-' );
}

function checkBox( e ) {
	let s = t0.dataset.id + '/';
	if ( c0 && c0 != this ) {
		c0.checked = 0;
	}
	c0 = this;
	if ( this.checked ) {
		s += this.parentNode.parentNode.dataset.id
	}
	fetch( '/cert.cgi/' + s, { method: 'PUT' } )
	.then( r => r.json() )
	.then( r => {
		if ( r.code !== 0 ) this.checked = 0;
	} );
}

function certRevoke( e ) {
	if ( window.confirm( 'Are you sure to revoke this certificate?' ) ) {
		fetch( this.href, { method: 'DELETE' } )
		.then( r => { location.reload() } );
	}
	e.preventDefault();
	return false;
}

function certUnrevoke( e ) {
	if ( window.confirm( 'Are you sure to un-revoke this certificate?' ) ) {
		fetch( this.href, { method: 'POST' } )
		.then( r => { location.reload() } );
	}
	e.preventDefault();
	return false;
}


function addRow( id, data ) {
	let el;
	let row = t0.tBodies[0].insertRow();
	for ( let j = 0; j < 7; j++ ) row.insertCell();

	row.dataset.id = id;

	el = document.createElement( 'input' );
	el.type = 'checkbox';
	if ( data.current ) {
		if ( c0 ) c0.checked = 0;
		c0 = el;
		el.checked = 1;
	}
	el.addEventListener( 'change', checkBox );
	row.cells[0].appendChild( el );
	
	/*el = document.createElement( 'span' );
	el.innerHTML = 'Download: ';
	row.cells[1].appendChild( el );*/

	el = document.createElement( 'a' );
	el.href = '/dl.cgi/' + t0.dataset.id + '/' + id;
	el.download = t0.dataset.id + '.ovpn';
	el.innerHTML = 'OVPN';
	row.cells[1].appendChild( el );

	el = document.createElement( 'span' );
	el.innerHTML = ' | ';
	row.cells[1].appendChild( el );

	el = document.createElement( 'a' );
	el.href = '/dl.cgi/' + t0.dataset.id + '/' + id + '?type=txt';
	el.download = t0.dataset.id + '.txt';
	el.innerHTML = 'TXT';
	row.cells[1].appendChild( el );

	el = document.createElement( 'a' );
	el.href = '/cert.cgi/' + t0.dataset.id + '/' + id;
	if ( data.revoked ) {
		el.innerHTML = 'Unrevoke';
		el.addEventListener( 'click', certUnrevoke );
	} else {
		el.innerHTML = 'Revoke';
		el.addEventListener( 'click', certRevoke );
	}
	row.cells[2].appendChild( el );

	row.cells[3].innerHTML = data.serial;
	row.cells[4].innerHTML = formatDate( data.startdate );
	row.cells[5].innerHTML = formatDate( data.enddate );

	if ( data.revoked ) {
		row.className = 'crit';
		row.cells[6].innerHTML = formatDate( data.revoked );
	} else if ( data.enddate - now < 0 ) {
		row.className = 'mask';
	} else if ( data.enddate - now < 7 * 86400 ) {
		row.className = 'warn';
	}
}


a1.addEventListener( 'click', e => {
	if ( window.confirm( 'Issue new certificate?' ) ) {
		fetch( '/cert.cgi/' + t0.dataset.id + '/', { method: 'POST' } )
		.then( r => r.json() )
		.then( r => {
			if ( r.code === 0 ) {
				addRow( r.id, r );
			}
		} );
	}
	e.preventDefault();
	return false;
} );

fetch( '/cert.cgi/' + t0.dataset.id )
.then( r => r.json() )
.then( r => {
	for ( let i in r ) {
		addRow( i, r[i] );
	}
} );
