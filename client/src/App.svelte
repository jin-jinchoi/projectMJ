<script lang="ts">
	import Diffusers from "./lib/Diffusers.svelte";
	import CompyUI from "./lib/CompyUI.svelte";
	import { Router, Link, Route } from "svelte-routing";
	import { writable } from "svelte/store";
	import { onMount } from "svelte";

	export let url = "";

	const currentPath = writable("/");

	onMount(() => {
		currentPath.set(window.location.pathname);

		const handleRouteChange = () => {
			currentPath.set(window.location.pathname);
		};

		window.addEventListener("popstate", handleRouteChange);

		return () => {
			window.removeEventListener("popstate", handleRouteChange);
		};
	});

	function isActive(path: string) {
		return $currentPath === path;
	}

	function handleLinkClick(path: string) {
		currentPath.set(path);
	}
</script>

<Router {url}>
	<div class="min-h-screen px-4 py-8 bg-white">
		<div class="max-w-6xl mx-auto">
			<nav class="flex items-center justify-center gap-4 p-4 mb-6">
				<Link
					to="/"
					class="px-6 py-2 text-lg rounded-lg font-bold {isActive('/')
						? 'text-white bg-blue-500 border border-blue-500'
						: 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'}"
					on:click={() => handleLinkClick("/")}
				>
					CompyUI (WebSocket)
				</Link>
				<Link
					to="/diffusers"
					class="px-6 py-2 text-lg rounded-lg font-bold {isActive('/diffusers')
						? 'text-white bg-blue-500 border border-blue-500'
						: 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'}"
					on:click={() => handleLinkClick("/diffusers")}
				>
					Diffusers
				</Link>
			</nav>

			<div>
				<Route path="/">
					<CompyUI />
				</Route>
				<Route path="/diffusers">
					<Diffusers />
				</Route>
			</div>
		</div>
	</div>
</Router>
