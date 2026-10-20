const b=document.getElementById("cart-drawer");if(b){let q=function(){try{const e=JSON.parse(localStorage.getItem(H)||"{}");Object.keys(f).forEach(t=>{const a=f[t];a&&!a.value&&typeof e[t]=="string"&&(a.value=e[t])})}catch{}},R=function(){try{const e={};Object.keys(f).forEach(t=>{e[t]=f[t].value.trim()}),localStorage.setItem(H,JSON.stringify(e))}catch{}},N=function(){w.classList.add("hidden"),w.textContent="",b.querySelectorAll("input.border-red-500").forEach(e=>{e.classList.remove("border-red-500"),e.classList.add("border-parrilla-border")})},p=function(e,t){w.textContent=e,w.classList.remove("hidden"),t&&(t.classList.remove("border-parrilla-border"),t.classList.add("border-red-500"),t.focus())},P=function(){const e=g.value,t=e==="Domicilio",a=e==="Mesa",r=O.value==="Efectivo";ie.classList.toggle("hidden",!a),ce.classList.toggle("hidden",!t),le.classList.toggle("hidden",!t),de.classList.toggle("hidden",!t),ue.classList.toggle("hidden",!(t&&r)),N()},X=function(e,t,a){n.push({id:`${Date.now()}${Math.random().toString(36).slice(2,9)}`,name:e,price:t,customizable:a,soup:a?u.sopa:null,principle:a?u.principios?.[0]??"Sin Principio":null,side:a?u.acompanamientos?.[0]??"Sin Acompañamiento":null,salad:a?"Con ensalada":null}),z(),E()},Z=function(e){n=n.filter(t=>t.id!==e),E()},z=function(){h.classList.add("bg-green-100"),setTimeout(()=>h.classList.remove("bg-green-100"),300)},$=function(e,t,a,r){return`
        <div class="flex items-center justify-between gap-2 text-sm">
          <label class="text-parrilla-muted font-medium">${e}:</label>
          <select class="item-select ${he}" data-field="${t}" data-id="${a}">${r}</select>
        </div>`},ee=function(e){let t=`
        <div class="flex items-center justify-between gap-2">
          <div class="min-w-0">
            <span class="block font-semibold text-sm text-parrilla-ivory">${I(e.name)}</span>
            <span class="block text-xs font-bold text-parrilla-gold mt-0.5">${i(e.price)}</span>
          </div>
          <button type="button" class="btn-remove-item flex items-center justify-center w-11 h-11 text-parrilla-muted hover:text-red-600 transition" data-id="${e.id}" aria-label="Quitar ${I(e.name)}">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>`;if(e.customizable){const a=A([{value:u.sopa,label:u.sopa},{value:"Sin Sopa",label:"Sin sopa"}],e.soup),r=A([...u.principios.map(d=>({value:d,label:d})),{value:"Sin Principio",label:"Sin principio"}],e.principle),c=A([...u.acompanamientos.map(d=>({value:d,label:d})),{value:"Sin Acompañamiento",label:"Sin acompañamiento"}],e.side),m=A([{value:"Con ensalada",label:"Con ensalada"},{value:"Sin ensalada",label:"Sin ensalada"}],e.salad);t+=`
          <div class="flex flex-col gap-1.5 mt-2.5 pt-2.5 border-t border-dashed border-parrilla-border">
            ${$("Sopa","soup",e.id,a)}
            ${$("Principio","principle",e.id,r)}
            ${$("Acompañamiento","side",e.id,c)}
            ${$("Ensalada","salad",e.id,m)}
          </div>`}return t},E=function(){if(L.innerHTML="",n.length===0){b.classList.add("hidden"),T.classList.add("hidden"),h.setAttribute("aria-expanded","false"),F.setAttribute("data-lucide","chevron-up"),document.body.classList.remove("pb-28"),j();return}b.classList.remove("hidden"),document.body.classList.add("pb-28"),n.forEach(r=>{const c=document.createElement("div");c.className="bg-slate-50 border border-parrilla-border rounded-lg p-3",c.innerHTML=ee(r),L.appendChild(c)});const e=n.reduce((r,c)=>r+c.price,0),t=J()?n.length*B:0,a=e+t;pe.textContent=i(e),me.textContent=i(t),be.textContent=i(a),G.classList.toggle("hidden",t===0),G.classList.toggle("flex",t>0),ae.textContent=`${n.length} plato${n.length>1?"s":""}`,oe.textContent=i(a),j()};const u=JSON.parse(b.dataset.specials||"{}"),te=b.dataset.whatsapp,o=e=>document.getElementById(e),h=o("cart-summary-trigger"),T=o("cart-details-panel"),L=o("cart-items-list"),ae=o("cart-count"),oe=o("cart-total"),F=o("cart-chevron"),se=o("clear-cart-btn"),ne=o("whatsapp-checkout-btn"),g=o("cart-service-type"),y=o("cart-customer-name"),S=o("cart-customer-phone"),D=o("cart-table-number"),x=o("cart-customer-address"),C=o("cart-customer-neighborhood"),re=o("cart-cutlery"),O=o("cart-payment-method"),k=o("cart-cash-amount"),ie=o("field-table"),ce=o("field-address"),le=o("field-neighborhood"),de=o("field-cutlery"),ue=o("field-cash-amount"),w=o("cart-form-error"),pe=o("summary-subtotal"),me=o("summary-empaque"),be=o("summary-total"),G=o("empaque-row"),B=1e3,i=e=>`$${e.toLocaleString("es-CO")}`,I=e=>String(e).replace(/[&<>"']/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[t]),j=()=>{window.lucide&&window.lucide.createIcons()};let n=[];const H="sanParrillaCustomer",f={name:y,phone:S,address:x,neighborhood:C};Object.values(f).forEach(e=>e.addEventListener("input",R)),[y,S,D,x,C,k].forEach(e=>e.addEventListener("input",N));const J=()=>g.value==="Domicilio"||g.value==="Recoger",he="w-40 min-h-[36px] px-2 py-1 bg-white rounded-md border border-parrilla-border text-sm text-parrilla-ivory focus:border-parrilla-gold outline-none cursor-pointer",A=(e,t)=>e.map(a=>`<option value="${I(a.value)}" ${t===a.value?"selected":""}>${I(a.label)}</option>`).join("");document.addEventListener("click",e=>{const t=e.target.closest(".btn-add-cart");if(!t||t.disabled)return;const a=parseInt(t.dataset.price,10);Number.isNaN(a)||X(t.dataset.name,a,t.dataset.customizable==="true")}),L.addEventListener("click",e=>{const t=e.target.closest(".btn-remove-item");t&&Z(t.dataset.id)}),L.addEventListener("change",e=>{const t=e.target.closest(".item-select");if(!t)return;const a=n.find(r=>r.id===t.dataset.id);a&&(a[t.dataset.field]=t.value)}),h.addEventListener("click",()=>{T.classList.toggle("hidden");const e=!T.classList.contains("hidden");h.setAttribute("aria-expanded",String(e)),F.setAttribute("data-lucide",e?"chevron-down":"chevron-up"),e&&q(),j()}),g.addEventListener("change",()=>{P(),E()}),O.addEventListener("change",P),se.addEventListener("click",()=>{n=[],E()}),ne.addEventListener("click",()=>{if(n.length===0)return;const e=g.value,t=e==="Domicilio",a=e==="Mesa",r=n.reduce((l,M)=>l+M.price,0),c=J()?n.length*B:0,m=r+c,d=O.value,U=d==="Efectivo";N();const _=y.value.trim(),K=S.value.trim(),Q=D.value.trim(),V=x.value.trim(),Y=C.value.trim(),W=k.value.replace(/\D/g,""),v=W?parseInt(W,10):0;if(!_)return p("Por favor escribe tu nombre.",y);if(!K)return p("Por favor escribe tu teléfono.",S);if(a&&!Q)return p("Indica el número de tu mesa.",D);if(t&&!V)return p("Escribe la dirección completa de entrega.",x);if(t&&!Y)return p("Escribe tu barrio o indicaciones de entrega.",C);if(t&&U&&v>0&&v<m)return p(`El monto con el que pagas debe ser mayor o igual al total (${i(m)}).`,k);R();let s=`🛒 *NUEVO PEDIDO - SAN PARRILLA*

`;s+=`👤 *Nombre:* ${_}
`,s+=`📞 *Teléfono:* ${K}
`,s+=`${t?"🛵":e==="Recoger"?"🛍️":"🍽️"} *Tipo de Servicio:* ${e}
`,a&&(s+=`🪑 *Mesa:* ${Q}
`),t&&(s+=`📍 *Dirección:* ${V}
`,s+=`🏘️ *Barrio / Indicaciones:* ${Y}
`,s+=`🍴 *Cubiertos plásticos:* ${re.value}
`),s+=`
💳 *Método de pago:* ${d}
`,t&&U&&v>0&&(s+=`💵 *Paga con:* ${i(v)} (cambio: ${i(v-m)})
`),s+=`
📋 *PEDIDO*

`,n.forEach((l,M)=>{s+=`*${M+1}. ${l.name}* (${i(l.price)})
`,l.customizable&&(s+=`   🥣 Sopa: ${l.soup||"No elegida"}
`,s+=`   🍚 Principio: ${l.principle||"No elegido"}
`,s+=`   🍟 Acompañante: ${l.side||"No elegido"}
`,s+=`   🥗 Ensalada: ${l.salad||"Con ensalada"}
`),s+=`
`}),s+=`🧾 *Subtotal:* ${i(r)}
`,c>0&&(s+=`📦 *Costo de Empaque:* ${i(c)} ($1.000 x ${n.length} artículo${n.length>1?"s":""})
`),s+=`💰 *TOTAL A PAGAR:* ${i(m)}

`,s+="¡Muchas gracias! Espero mi confirmación del pedido por este medio.",window.open(`https://wa.me/${te}?text=${encodeURIComponent(s)}`,"_blank")}),q(),P()}
