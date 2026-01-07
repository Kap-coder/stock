// PWA helper: register service worker, queue operations in IndexedDB and sync when online
(function(){
  if ('serviceWorker' in navigator) {
    // register service worker at site root so its scope covers the whole app
    navigator.serviceWorker.register('/sw.js').then(reg => {
      console.log('SW registered', reg);
    }).catch(err => console.warn('SW register failed', err));
  }

  // Simple IndexedDB wrapper
  function openDB(){
    return new Promise((resolve, reject) => {
      const req = indexedDB.open('g_business_pwa', 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains('sync-queue')) db.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function addToQueue(item){
    const db = await openDB();
    return new Promise((res, rej) => {
      const tx = db.transaction('sync-queue', 'readwrite');
      const store = tx.objectStore('sync-queue');
      store.add(item);
      tx.oncomplete = () => res(true);
      tx.onerror = () => rej(tx.error);
    });
  }

  async function getAllQueue(){
    const db = await openDB();
    return new Promise((res, rej) => {
      const tx = db.transaction('sync-queue', 'readonly');
      const store = tx.objectStore('sync-queue');
      const req = store.getAll();
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
  }

  async function clearQueue(){
    const db = await openDB();
    return new Promise((res, rej) => {
      const tx = db.transaction('sync-queue', 'readwrite');
      const store = tx.objectStore('sync-queue');
      store.clear();
      tx.oncomplete = () => res(true);
      tx.onerror = () => rej(tx.error);
    });
  }

  function getCSRF(){
    const m = document.cookie.match('(^|;)\\s*' + 'csrftoken' + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  async function trySync(){
    if (!navigator.onLine) return false;
    const queue = await getAllQueue();
    if (!queue || queue.length === 0) return true; // nothing to sync

    const ops = queue.map(q => q.payload);
    try{
      // show syncing toast
      showToast('Synchronisation...', 'info');

      const res = await fetch('/api/sync/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRF()
        },
        body: JSON.stringify({ operations: ops })
      });
      if (res.ok){
        await clearQueue();
        console.log('PWA: Synced queue');
        // notify service worker to update caches if needed
        if (navigator.serviceWorker && navigator.serviceWorker.controller){
          navigator.serviceWorker.controller.postMessage({ type: 'SYNC_NOW' });
        }
        showToast('Vous êtes de nouveau en ligne.', 'success');
        return true;
      } else {
        const text = await res.text();
        console.warn('PWA: sync failed', text);
        showToast('Synchronisation échouée.', 'error');
        return false;
      }
    } catch(e){
      console.warn('PWA: sync error', e);
      showToast('Synchronisation échouée.', 'error');
      return false;
    }
  }

  // Public API: queue a sale (example)
  window.PWA = {
    queueSale: async function(sale){
      await addToQueue({ type: 'op', payload: { type: 'sale', payload: sale, queued_at: Date.now() } });
      trySync();
    }
  };

  window.addEventListener('online', trySync);
  // Try immediately on load
  trySync();
  // Toast helper
  function ensureToastContainer(){
    let c = document.getElementById('pwa-toast-container');
    if (c) return c;
    c = document.createElement('div');
    c.id = 'pwa-toast-container';
    c.style.position = 'fixed';
    c.style.top = '1rem';
    c.style.right = '1rem';
    c.style.zIndex = 99999;
    document.body.appendChild(c);
    return c;
  }

  function showToast(message, type){
    const container = ensureToastContainer();
    const el = document.createElement('div');
    el.textContent = message;
    el.style.marginTop = '0.5rem';
    el.style.padding = '0.75rem 1rem';
    el.style.borderRadius = '8px';
    el.style.color = '#fff';
    el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
    el.style.fontFamily = 'sans-serif';
    el.style.fontSize = '14px';
    if (type === 'error') el.style.background = '#e11d48';
    else if (type === 'success') el.style.background = '#10b981';
    else el.style.background = '#2563eb';
    container.appendChild(el);
    setTimeout(()=>{
      el.style.transition = 'opacity 300ms';
      el.style.opacity = '0';
      setTimeout(()=>el.remove(), 300);
    }, 3500);
  }

  // Show offline/online messages
  window.addEventListener('offline', () => {
    showToast('Vous êtes en hors-ligne.', 'error');
  });

  // On online event, try sync and show messages in trySync
  window.addEventListener('online', async () => {
    await trySync();
  });
  // INSTALL PROMPT HANDLING
  let deferredPrompt = null;
  const installModal = () => document.getElementById('pwa-install-modal');
  const showInstallModal = () => {
    const el = installModal(); if (!el) return;
    el.classList.remove('hidden'); el.classList.add('flex');
  };
  const hideInstallModal = () => {
    const el = installModal(); if (!el) return;
    el.classList.add('hidden'); el.classList.remove('flex');
  };

  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    deferredPrompt = e;

    // Only show if not already installed and not dismissed recently
    const installed = localStorage.getItem('pwa_installed');
    const dismissed = localStorage.getItem('pwa_install_dismissed');
    if (installed) return;
    if (dismissed) {
      const ts = parseInt(dismissed, 10);
      // don't show again for 24 hours
      if (Date.now() - ts < 24 * 3600 * 1000) return;
    }

    showInstallModal();
  });

  // Wire modal buttons
  document.addEventListener('click', async (ev) => {
    const t = ev.target;
    if (!t) return;

    if (t.id === 'pwa-install-btn'){
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice && choice.outcome === 'accepted'){
        localStorage.setItem('pwa_installed', '1');
      } else {
        localStorage.setItem('pwa_install_dismissed', Date.now().toString());
      }
      hideInstallModal();
      deferredPrompt = null;
    }

    if (t.id === 'pwa-install-dismiss' || t.id === 'pwa-install-close'){
      localStorage.setItem('pwa_install_dismissed', Date.now().toString());
      hideInstallModal();
    }
  });

  // When app is installed
  window.addEventListener('appinstalled', (evt) => {
    localStorage.setItem('pwa_installed', '1');
    hideInstallModal();
  });

})();
