	
	// requires https://momentjs.com/
	// working fiddlejs : https://jsfiddle.net/38bL1q09/3/
	
	// set the start date (should be first day of a year)
	var startDate = moment(new Date('1981-01-01'))
	// set the number of months to compute (years*12) 
	var nbMonths = 480
	
	var dekads = []
	
	for (let i = 0; i < nbMonths; i++) {
		createDekad(i)
	}
	
	function createDekad(i){
		var sd1 = moment(startDate).add(i,'months').format('YYYY-MM-DD');
		var ed1 = moment(startDate).add(i,'months').add(9,'days').format('YYYY-MM-DD');
		var years = Number(moment(sd1).format('YYYY'))-Number(moment(startDate).format('YYYY'))
		var id1 = ((i-(years*12))*3)+1
		
		
		var sd2 = moment(startDate).add(i,'months').add(10,'days').format('YYYY-MM-DD');
		var ed2 = moment(startDate).add(i,'months').add(19,'days').format('YYYY-MM-DD');
		var id2 = id1+1
		
		var sd3 = moment(startDate).add(i,'months').add(20,'days').format('YYYY-MM-DD');
		var daysInMonth = moment(sd3).daysInMonth();
		var dekal3Lenght = daysInMonth-20
		var ed3 = moment(startDate).add(i,'months').add(19+dekal3Lenght,'days').format('YYYY-MM-DD');
		var id3 = id1+2
	
        dekads.push({
			id:moment(sd1).format('YYYY')+"-"+id1,
			sd:sd1,
			ed:ed1,
			nd:10
		})	
		dekads.push({
			id:moment(sd1).format('YYYY')+"-"+id2,
			sd:sd2,
			ed:ed2,
			nd:10
		})	
		dekads.push({
			id:moment(sd1).format('YYYY')+"-"+id3,
			sd:sd3,
			ed:ed3,
			nd:dekal3Lenght
		})			
	}
	
	console.log(dekads)