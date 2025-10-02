let mouseIdleTimer,isIdle=!1;const IDLE_TIME=5e3,btn1=document.getElementById("btn1"),btn2=document.getElementById("btn2");function resetIdleTimer(){clearTimeout(mouseIdleTimer),isIdle&&(btn1.classList.remove("idle-bounce"),btn2.classList.remove("idle-pulse"),isIdle=!1),mouseIdleTimer=setTimeout(()=>{isIdle||(btn1.classList.add("idle-bounce"),btn2.classList.add("idle-pulse"),isIdle=!0)},IDLE_TIME)}document.addEventListener("mousemove",resetIdleTimer),document.addEventListener("click",resetIdleTimer),document.addEventListener("keypress",resetIdleTimer);function createParticles(e,t){for(let e=0;e<6;e++)setTimeout(()=>{const e=document.createElement("div");e.className="particle",e.style.left=Math.random()*100+"%",e.style.animationDelay=Math.random()*2+"s",t.appendChild(e),setTimeout(()=>{e.remove()},3e3)},e*100)}btn1.addEventListener("mouseenter",()=>{const e=document.getElementById("particles1");createParticles(btn1,e)}),btn2.addEventListener("mouseenter",()=>{const e=document.getElementById("particles2");createParticles(btn2,e)}),resetIdleTimer();function addClickEffect(e){e.addEventListener("click",t=>{t.preventDefault();const o=document.createElement("div"),n=e.getBoundingClientRect(),s=Math.max(n.width,n.height),i=t.clientX-n.left-s/2,a=t.clientY-n.top-s/2;o.style.cssText=`
            position: absolute;
            width: ${s}px;
            height: ${s}px;
            left: ${i}px;
            top: ${a}px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `,e.appendChild(o),setTimeout(()=>{o.remove()},600),setTimeout(()=>{window.location.href=e.href},300)})}const style=document.createElement("style");style.textContent=`
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`,document.head.appendChild(style),addClickEffect(btn1),addClickEffect(btn2)