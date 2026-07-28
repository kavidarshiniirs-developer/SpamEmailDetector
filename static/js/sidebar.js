function toggleSidebar() {

    const sidebar = document.getElementById("sidebar");
    const main = document.querySelector(".main");
    const button = document.getElementById("menuBtn");

    sidebar.classList.toggle("hide");
    main.classList.toggle("full");

    if(sidebar.classList.contains("hide")){

        button.innerHTML='<i class="fa-solid fa-bars"></i>';

    }else{

        button.innerHTML='<i class="fa-solid fa-xmark"></i>';

    }

}