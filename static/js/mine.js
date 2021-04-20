function projects_init(){
    console.log("in Init");
    ob = new obj();
    ob.getprojects();
    setInterval(ob.getprojects, 120000);
}

function obj(){
    this.getprojects = function(){
        console.log('in getProducts');
        ob.clearproducts();
        console.log('Cleared');
        var xhr = new XMLHttpRequest();
        xhr.open('GET','/getprojects',true);
		val = "{{session['access_token']}}";
		console.log("Access token:{{ session['access_token'] }}")
		xhr.setRequestHeader("Authorization", "Bearer "+val)
        xhr.onreadystatechange = ob.setproducts;
        xhr.send();
    },
    this.setproducts = function(){
        if(this.status==200 && this.readyState==4){
            console.log('in setProjects');
            if(JSON.parse(this.responseText)['msg']=='Empty'){
            	grid = document.getElementById("myprojects");
            	grid.remove();
            	inp = document.getElementById("myprojects");
            	inp.remove();
            }
            else{
                var df = JSON.parse(this.responseText);
                grid=document.getElementById("myprojects");
                for(var i=0;i<Object.keys(df).length;i++){
                    data = JSON.parse(df[i]);
                	div1 = document.createElement('div');
                    div1.classList.value = "card";
                    image_div = document.createElement("div");
                    image_div.classList.value = "card_image";
                    img1 = document.createElement("img");
                    img1.src = "https://i.redd.it/b3esnz5ra34y.jpg";
                    title_div = document.createElement("div");
                    title_div.classList.value = "card_title title-white";
                    p1 = document.createElement("p");
                    p1.innerHTML = data['name'];
                    title_div.appendChild(p1);
                    image_div.appendChild(img1);
                    div1.appendChild(image_div);                  
                    div1.appendChild(title_div);
                    grid.appendChild(div1);
                }
            }
        }
    },
    this.clearproducts = function(){
        const myNode = document.getElementById("myprojects");
        while (myNode.firstChild) {
            myNode.removeChild(myNode.lastChild);
        }
    }
}