import { useState, useEffect } from 'react';
import { useScroll, useTransform, motion } from 'framer-motion';
import Header from './Header';
import ThematicHero from './ThematicHero';
import MassiveSearch from './MassiveSearch';
import TrendingFoods from './TrendingFoods';
import CuisineCategories from './CuisineCategories';
import ChefStoriesAndMap from './ChefStoriesAndMap';
import ExploreNearby from './ExploreNearby';
import FloatingFoodParallax from './FloatingFoodParallax';
import RecipeModal from './RecipeModal';
import RestaurantMenuModal from './RestaurantMenuModal';

export default function HomePage(props) {
  const userCity = props.userCity;
  const userCountry = props.userCountry;
  const userPosition = props.userPosition;
  const onSearch = props.onSearch;
  const onViewStories = props.onViewStories;
  const onCookChat = props.onCookChat;
  const onOpenProfile = props.onOpenProfile;

  const { scrollY } = useScroll();
  const backgroundY = useTransform(scrollY, [0, 1000], [0, 150]);
  const [navigationTarget, setNavigationTarget] = useState(null);

  const handleRouteSelect = (routeObj) => {
    setNavigationTarget(routeObj);
    window.scrollTo({ top: document.body.scrollHeight / 2, behavior: 'smooth' });

    window.dispatchEvent(new CustomEvent('frog-speak', { detail: 'Starting navigation to ' + routeObj.name + ' by ' + routeObj.mode + '. Lets go!' }));

    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('frog-speak', { detail: 'Head straight down the street, it smells great this way.' }));
    }, 5000);

    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('frog-speak', { detail: 'We have arrived at ' + routeObj.name + '! Enjoy your food!' }));
    }, 12000);
  };

  return (
    <div style={{ width: '100vw', overflowX: 'hidden', position: 'relative', background: '#FFF6EC' }}>

      <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 0, pointerEvents: 'none', backgroundImage: 'radial-gradient(circle at 50% 20%, rgba(255, 122, 48, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 60%, rgba(211, 47, 47, 0.03) 0%, transparent 40%)' }}>
        <FloatingFoodParallax scrollY={backgroundY} />
      </div>

      <div style={{ position: 'relative', zIndex: 10 }}>
        <Header onSearch={onSearch} onOpenProfile={onOpenProfile} />
        <ThematicHero />

        <MassiveSearch
          onSearch={onSearch}
          onSubmitSearch={() => {
            const el = document.getElementById('cuisine-categories');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }}
        />

        <TrendingFoods userCity={userCity} userCountry={userCountry} onCookChat={onCookChat} />

        <CuisineCategories userCity={userCity} userCountry={userCountry} onCookChat={onCookChat} />

        <ChefStoriesAndMap onViewAllStories={onViewStories} onCookChat={onCookChat} navigationTarget={navigationTarget} userPosition={userPosition} onExploreClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })} />

        <ExploreNearby onRouteSelect={handleRouteSelect} userPosition={userPosition} />
      </div>

      <RecipeModal />
      <RestaurantMenuModal />
    </div>
  );
}
